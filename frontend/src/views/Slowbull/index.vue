<template>
  <div class="slowbull-page">
    <div class="slowbull-header">
      <div class="title">
        <el-icon><TrendCharts /></el-icon>
        <span>慢牛策略看板</span>
      </div>
      <div class="actions">
        <el-button text size="small" @click="reloadFrame">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button text size="small" tag="a" :href="viewerUrl" target="_blank" rel="noopener">
          <el-icon><TopRight /></el-icon> 新窗口打开
        </el-button>
      </div>
    </div>
    <div class="slowbull-desc">
      A 股慢牛主线集中持仓策略的只读看板（持仓赛道、转化分、退出条件、实盘净值）。数据来自策略实盘系统，只读展示。
    </div>

    <div class="frame-wrap" v-loading="loading">
      <iframe
        ref="frameRef"
        :src="viewerUrl"
        class="viewer-frame"
        @load="loading = false"
        title="慢牛策略看板"
      ></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { TrendCharts, Refresh, TopRight } from '@element-plus/icons-vue'

// slowbull 公开只读看板（Cloudflare Tunnel 暴露的 viewer）
// ?embed=true: Streamlit 嵌入模式，隐藏顶部菜单/页脚，更干净
const viewerUrl = 'https://viewer.knowulearning.com/?embed=true'
const loading = ref(true)
const frameRef = ref<HTMLIFrameElement | null>(null)

const reloadFrame = () => {
  loading.value = true
  if (frameRef.value) {
    // 重新赋 src 触发刷新
    const u = frameRef.value.src
    frameRef.value.src = 'about:blank'
    setTimeout(() => { if (frameRef.value) frameRef.value.src = u }, 50)
  }
}
</script>

<style lang="scss" scoped>
.slowbull-page {
  padding: 24px;
  min-height: 100vh;
  background: var(--el-bg-color-page);
  display: flex;
  flex-direction: column;
}
.slowbull-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.slowbull-header .title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 700;
}
.slowbull-desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}
.frame-wrap {
  flex: 1;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  min-height: 70vh;
}
.viewer-frame {
  width: 100%;
  height: 100%;
  min-height: 70vh;
  border: 0;
  display: block;
}
</style>
