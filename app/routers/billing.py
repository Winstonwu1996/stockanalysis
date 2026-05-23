"""
计费 / 会员路由 (Billing & Membership)

W-Agents SaaS 收费骨架。参照 VocabSpark：Stripe Checkout（一次性付款）+ 优惠码 + webhook。
- 用 httpx 直接调 Stripe REST（不加 stripe SDK 依赖）
- webhook 用 stdlib HMAC 验签
- 未配置 STRIPE_SECRET_KEY 时，checkout/webhook 返回"支付未配置"，不影响其它功能

环境变量（William 上线收费时在 .env 配）:
  STRIPE_SECRET_KEY        sk_live_... 或 sk_test_...
  STRIPE_WEBHOOK_SECRET    whsec_...
  STRIPE_PRICE_PRO_MONTHLY price_xxx   (月付价格ID)
  STRIPE_PRICE_PRO_YEARLY  price_xxx   (年付价格ID)
  BILLING_SUCCESS_URL      支付成功跳转 (默认 https://bull.knowulearning.com/billing?success=1)
  BILLING_CANCEL_URL       取消跳转
"""

import os
import json
import hmac
import hashlib
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from .auth_db import get_current_user
from app.services.membership_service import membership_service, FREE_DAILY_ANALYSIS_LIMIT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])

STRIPE_API = "https://api.stripe.com/v1"


def _stripe_key() -> Optional[str]:
    k = os.getenv("STRIPE_SECRET_KEY", "").strip()
    return k if k and not k.startswith("your") else None


# ---------- 套餐定义 ----------
PLANS = {
    "free": {
        "name": "免费体验",
        "price_monthly": 0,
        "features": [f"每天 {FREE_DAILY_ANALYSIS_LIMIT} 次个股分析", "查看分析报告"],
    },
    "pro": {
        "name": "专业会员",
        "price_monthly": 29,   # 展示用，真实金额以 Stripe 价格为准
        "price_yearly": 288,
        "features": ["无限个股分析", "报告下载 (PDF/Word/MD)", "报告追问讨论", "慢牛策略看板", "深度模型 (DeepSeek V4 Pro)"],
    },
}


class CheckoutRequest(BaseModel):
    billing_cycle: str = "monthly"  # monthly | yearly


@router.get("/plans")
async def get_plans():
    """套餐列表（公开）。"""
    return {"success": True, "data": PLANS, "payment_enabled": _stripe_key() is not None}


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    """当前用户的会员状态 + 今日用量。"""
    username = user.get("username")
    m = membership_service.get_membership(username)
    used = membership_service.get_today_usage(username)
    return {
        "success": True,
        "data": {
            **m,
            "today_used": used,
            "free_daily_limit": FREE_DAILY_ANALYSIS_LIMIT,
            "payment_enabled": _stripe_key() is not None,
        },
    }


@router.post("/checkout")
async def create_checkout(body: CheckoutRequest, user: dict = Depends(get_current_user)):
    """创建 Stripe Checkout 会话，返回支付链接。未配置 Stripe 时返回 503。"""
    key = _stripe_key()
    if not key:
        raise HTTPException(status_code=503, detail="支付通道未配置（请联系管理员配置 Stripe）")

    cycle = body.billing_cycle if body.billing_cycle in ("monthly", "yearly") else "monthly"
    price_id = os.getenv(
        "STRIPE_PRICE_PRO_YEARLY" if cycle == "yearly" else "STRIPE_PRICE_PRO_MONTHLY", ""
    ).strip()
    if not price_id:
        raise HTTPException(status_code=503, detail=f"未配置 {cycle} 价格ID（STRIPE_PRICE_PRO_*）")

    success_url = os.getenv("BILLING_SUCCESS_URL", "https://bull.knowulearning.com/billing?success=1")
    cancel_url = os.getenv("BILLING_CANCEL_URL", "https://bull.knowulearning.com/billing?canceled=1")
    username = user.get("username")

    # Stripe REST: 创建 checkout session (form-encoded)
    form = {
        "mode": "payment",
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "allow_promotion_codes": "true",  # 启用优惠码
        "success_url": success_url + "&session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
        "client_reference_id": username,
        "metadata[username]": username,
        "metadata[tier]": "pro",
        "metadata[billing_cycle]": cycle,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{STRIPE_API}/checkout/sessions",
                data=form,
                auth=(key, ""),
            )
        if resp.status_code >= 400:
            logger.error(f"Stripe checkout 失败: {resp.status_code} {resp.text[:300]}")
            raise HTTPException(status_code=502, detail="创建支付会话失败")
        data = resp.json()
        return {"success": True, "data": {"url": data.get("url"), "session_id": data.get("id")}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"checkout 异常: {e}")
        raise HTTPException(status_code=502, detail="支付服务异常")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Stripe webhook：支付成功 (checkout.session.completed) 时写入会员记录。"""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    # 验签（stdlib HMAC，避免引入 stripe SDK）
    if webhook_secret and not webhook_secret.startswith("your"):
        if not _verify_stripe_sig(payload, sig_header, webhook_secret):
            raise HTTPException(status_code=400, detail="签名验证失败")
    else:
        logger.warning("⚠️ STRIPE_WEBHOOK_SECRET 未配置，跳过验签（仅限测试）")

    try:
        event = json.loads(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="无效 payload")

    if event.get("type") == "checkout.session.completed":
        session = event.get("data", {}).get("object", {})
        meta = session.get("metadata", {}) or {}
        username = meta.get("username") or session.get("client_reference_id")
        cycle = meta.get("billing_cycle", "monthly")
        amount = session.get("amount_total", 0)
        currency = session.get("currency", "usd")
        if username:
            membership_service.record_subscription(
                username=username, tier="pro", billing_cycle=cycle,
                amount_paid=amount, currency=currency,
                stripe_session_id=session.get("id"),
            )
            logger.info(f"✅ webhook: {username} 升级 pro")

    return {"received": True}


def _verify_stripe_sig(payload: bytes, sig_header: str, secret: str) -> bool:
    """验证 Stripe webhook 签名 (t=...,v1=...)。"""
    try:
        parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
        timestamp = parts.get("t", "")
        expected = parts.get("v1", "")
        signed_payload = f"{timestamp}.".encode() + payload
        computed = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, expected)
    except Exception:
        return False
