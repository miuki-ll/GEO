<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="brand">
        <img src="/favicon.svg" alt="GEO" class="logo" />
        <div class="brand-text">
          <h1>创建企业账号</h1>
          <p>开启 AI 可见度运营之旅</p>
        </div>
      </div>
      <el-form :model="form" label-position="top" size="large">
        <el-form-item label="企业名称">
          <el-input v-model="form.enterprise" placeholder="例如：XX 皮肤管理中心" />
        </el-form-item>
        <el-form-item label="联系人姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="用于登录和接收通知" />
        </el-form-item>
        <el-form-item label="设置密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" class="submit-btn" @click="handleRegister">创建账号</el-button>
      </el-form>
      <div class="footer-tip">
        已有账号？
        <router-link to="/login">去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
const router = useRouter()
const form = reactive({
  enterprise: '',
  name: '',
  email: '',
  password: '',
})
function handleRegister() {
  ElMessage.success('MVP 占位：注册功能将在 S2 阶段实现')
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eaf2ff 0%, #f0faf3 50%, #fff6ea 100%);
  padding: 20px;
}
.auth-card {
  width: 100%;
  max-width: 480px;
  background: #fff;
  border-radius: 16px;
  padding: 36px 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.logo {
  width: 48px;
  height: 48px;
  border-radius: 10px;
}
.brand-text h1 {
  margin: 0;
  font-size: 20px;
  color: #1f2a44;
}
.brand-text p {
  margin: 4px 0 0;
  color: #909399;
  font-size: 12px;
}
.submit-btn {
  width: 100%;
  margin-top: 6px;
}
.footer-tip {
  margin-top: 18px;
  text-align: center;
  font-size: 13px;
  color: #909399;
}
</style>

