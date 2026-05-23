<template>
  <div class="billing-page">
    <div class="billing-head">
      <h2>会员与升级</h2>
      <p class="sub">解锁无限分析、报告下载、追问讨论与慢牛策略看板</p>
    </div>

    <!-- 当前状态 -->
    <el-card class="status-card" shadow="never" v-loading="loading">
      <div class="status-row">
        <div>
          <div class="label">当前套餐</div>
          <div class="value">
            <el-tag :type="status.tier === 'pro' ? 'success' : 'info'" size="large">
              {{ status.tier === 'pro' ? '专业会员' : '免费体验' }}
            </el-tag>
          </div>
        </div>
        <div v-if="status.tier !== 'pro'">
          <div class="label">今日已用</div>
          <div class="value">{{ status.today_used }} / {{ status.free_daily_limit }} 次分析</div>
        </div>
        <div v-if="status.tier === 'pro' && status.expires_at">
          <div class="label">到期</div>
          <div class="value">{{ formatDate(status.expires_at) }}</div>
        </div>
      </div>
    </el-card>

    <!-- 套餐对比 -->
    <div class="plans">
      <el-card class="plan-card" shadow="hover">
        <div class="plan-name">{{ plans.free?.name || '免费体验' }}</div>
        <div class="plan-price">¥0<span>/月</span></div>
        <ul class="plan-feats">
          <li v-for="(f, i) in plans.free?.features || []" :key="i">✓ {{ f }}</li>
        </ul>
        <el-button disabled style="width:100%">当前免费</el-button>
      </el-card>

      <el-card class="plan-card pro" shadow="hover">
        <div class="plan-badge">推荐</div>
        <div class="plan-name">{{ plans.pro?.name || '专业会员' }}</div>
        <div class="plan-price">¥{{ plans.pro?.price_monthly ?? 29 }}<span>/月</span></div>
        <ul class="plan-feats">
          <li v-for="(f, i) in plans.pro?.features || []" :key="i">✓ {{ f }}</li>
        </ul>
        <div class="cycle">
          <el-radio-group v-model="cycle" size="small">
            <el-radio-button label="monthly">月付</el-radio-button>
            <el-radio-button label="yearly">年付（更省）</el-radio-button>
          </el-radio-group>
        </div>
        <el-button
          type="primary"
          style="width:100%"
          :loading="checkoutLoading"
          :disabled="status.tier === 'pro'"
          @click="upgrade"
        >{{ status.tier === 'pro' ? '已是专业会员' : '升级到专业会员' }}</el-button>
        <p v-if="!paymentEnabled" class="hint">⚠️ 支付通道尚未开通，敬请期待</p>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(true)
const checkoutLoading = ref(false)
const cycle = ref<'monthly' | 'yearly'>('monthly')
const status = ref<any>({ tier: 'free', today_used: 0, free_daily_limit: 3 })
const plans = ref<any>({})
const paymentEnabled = ref(false)

const authHeaders = () => ({ Authorization: `Bearer ${authStore.token}`, 'Content-Type': 'application/json' })

const loadAll = async () => {
  loading.value = true
  try {
    const [s, p] = await Promise.all([
      fetch('/api/billing/status', { headers: authHeaders() }).then(r => r.json()),
      fetch('/api/billing/plans').then(r => r.json()),
    ])
    if (s.success) status.value = s.data
    if (p.success) { plans.value = p.data; paymentEnabled.value = p.payment_enabled }
  } catch (e) {
    console.error('加载会员信息失败', e)
  } finally {
    loading.value = false
  }
}

const upgrade = async () => {
  checkoutLoading.value = true
  try {
    const res = await fetch('/api/billing/checkout', {
      method: 'POST', headers: authHeaders(),
      body: JSON.stringify({ billing_cycle: cycle.value }),
    })
    const data = await res.json()
    if (res.ok && data.success && data.data?.url) {
      window.location.href = data.data.url   // 跳转 Stripe Checkout
    } else {
      ElMessage.warning(data.detail || data.message || '支付通道未开通，敬请期待')
    }
  } catch (e: any) {
    ElMessage.error('发起支付失败：' + (e.message || '未知错误'))
  } finally {
    checkoutLoading.value = false
  }
}

const formatDate = (s: string) => (s ? String(s).slice(0, 10) : '')

onMounted(loadAll)
</script>

<style lang="scss" scoped>
.billing-page { padding: 24px; min-height: 100vh; background: var(--el-bg-color-page); }
.billing-head h2 { margin: 0 0 4px; }
.billing-head .sub { color: var(--el-text-color-secondary); margin: 0 0 20px; }
.status-card { margin-bottom: 24px; }
.status-row { display: flex; gap: 48px; }
.status-row .label { color: var(--el-text-color-secondary); font-size: 13px; margin-bottom: 6px; }
.status-row .value { font-size: 16px; font-weight: 600; }
.plans { display: flex; gap: 20px; flex-wrap: wrap; }
.plan-card { width: 320px; position: relative; }
.plan-card.pro { border: 2px solid var(--el-color-primary); }
.plan-badge {
  position: absolute; top: 12px; right: 12px;
  background: var(--el-color-primary); color: #fff;
  font-size: 12px; padding: 2px 10px; border-radius: 10px;
}
.plan-name { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
.plan-price { font-size: 32px; font-weight: 800; margin-bottom: 16px; }
.plan-price span { font-size: 14px; font-weight: 400; color: var(--el-text-color-secondary); }
.plan-feats { list-style: none; padding: 0; margin: 0 0 18px; }
.plan-feats li { padding: 6px 0; color: var(--el-text-color-regular); }
.cycle { margin-bottom: 14px; }
.hint { color: var(--el-color-warning); font-size: 12px; margin: 10px 0 0; text-align: center; }
</style>
