"""
会员服务 (Membership Service)

W-Agents SaaS 会员体系，参照 VocabSpark 的 Stripe + 分层模式，原生实现在 FastAPI/Mongo。
设计为自包含模块：未配置 Stripe 时不影响现有功能；配置 STRIPE_SECRET_KEY 后即激活收费。

分层:
- free: 免费试用，每天 N 次个股分析 (默认 3)，不能下载/追问
- pro:  付费会员，无限分析 + 下载 + 追问 + 慢牛策略看板

数据:
- Mongo `user_memberships`: 一条/次订阅记录 (user 取 expires_at 最大且 active 的)
- Mongo `usage_daily`: {username, date, analysis_count} 免费额度计数
"""

import os
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# 免费层每日个股分析次数
FREE_DAILY_ANALYSIS_LIMIT = int(os.getenv("FREE_DAILY_ANALYSIS_LIMIT", "3"))

TIER_FREE = "free"
TIER_PRO = "pro"


def _db():
    from app.core.database import get_mongo_db_sync
    return get_mongo_db_sync()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _today_str() -> str:
    return _now().strftime("%Y-%m-%d")


class MembershipService:
    """会员状态查询 + 免费额度计数。纯同步，供 FastAPI 依赖/路由调用。"""

    @staticmethod
    def get_membership(username: str) -> dict:
        """返回用户当前会员状态。无有效订阅 → free。"""
        result = {"tier": TIER_FREE, "is_active": False, "expires_at": None, "billing_cycle": None}
        if not username:
            return result
        try:
            db = _db()
            # admin 永远算 pro (内部账号)
            user = db.users.find_one({"username": username})
            if user and user.get("is_admin"):
                return {"tier": TIER_PRO, "is_active": True, "expires_at": None, "billing_cycle": "admin"}

            doc = db.user_memberships.find_one(
                {"username": username, "status": "active"},
                sort=[("expires_at", -1)],
            )
            if doc:
                exp = doc.get("expires_at")
                active = bool(exp) and exp.replace(tzinfo=timezone.utc) >= _now() if isinstance(exp, datetime) else False
                if active:
                    result = {
                        "tier": doc.get("tier", TIER_PRO),
                        "is_active": True,
                        "expires_at": exp.isoformat() if isinstance(exp, datetime) else exp,
                        "billing_cycle": doc.get("billing_cycle"),
                    }
        except Exception as e:
            logger.warning(f"get_membership 失败({username}): {e}")
        return result

    @staticmethod
    def is_pro(username: str) -> bool:
        m = MembershipService.get_membership(username)
        return m["is_active"] and m["tier"] == TIER_PRO

    @staticmethod
    def record_subscription(username: str, tier: str, billing_cycle: str,
                            amount_paid: int = 0, currency: str = "usd",
                            stripe_session_id: str = None, days: int = None) -> bool:
        """记录一次成功订阅 (供 Stripe webhook 调用)。"""
        try:
            db = _db()
            if days is None:
                days = 365 if billing_cycle == "yearly" else 30
            now = _now()
            db.user_memberships.insert_one({
                "username": username,
                "tier": tier,
                "billing_cycle": billing_cycle,
                "amount_paid": amount_paid,
                "currency": currency,
                "stripe_session_id": stripe_session_id,
                "status": "active",
                "starts_at": now,
                "expires_at": now + timedelta(days=days),
                "created_at": now,
            })
            logger.info(f"✅ 记录订阅: {username} -> {tier}/{billing_cycle} (+{days}天)")
            return True
        except Exception as e:
            logger.error(f"record_subscription 失败({username}): {e}")
            return False

    # ---------- 免费额度 ----------
    @staticmethod
    def get_today_usage(username: str) -> int:
        try:
            db = _db()
            doc = db.usage_daily.find_one({"username": username, "date": _today_str()})
            return int(doc.get("analysis_count", 0)) if doc else 0
        except Exception:
            return 0

    @staticmethod
    def check_and_consume_analysis(username: str) -> dict:
        """检查并消费一次分析配额。返回 {allowed, tier, used, limit, message}。
        pro/admin 无限；free 受每日限额。"""
        if MembershipService.is_pro(username):
            return {"allowed": True, "tier": TIER_PRO, "used": 0, "limit": -1, "message": "pro 无限制"}
        used = MembershipService.get_today_usage(username)
        if used >= FREE_DAILY_ANALYSIS_LIMIT:
            return {
                "allowed": False, "tier": TIER_FREE, "used": used, "limit": FREE_DAILY_ANALYSIS_LIMIT,
                "message": f"免费版每天 {FREE_DAILY_ANALYSIS_LIMIT} 次分析已用完，升级会员可无限使用",
            }
        # 消费一次
        try:
            db = _db()
            db.usage_daily.update_one(
                {"username": username, "date": _today_str()},
                {"$inc": {"analysis_count": 1}, "$setOnInsert": {"created_at": _now()}},
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"消费配额失败({username}): {e}")
        return {"allowed": True, "tier": TIER_FREE, "used": used + 1, "limit": FREE_DAILY_ANALYSIS_LIMIT, "message": "ok"}


membership_service = MembershipService()
