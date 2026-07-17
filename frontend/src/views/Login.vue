<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="brand">
        <img src="/favicon.svg" alt="GEO" class="logo" />
        <div class="brand-text">
          <h1>GEO 运营平台</h1>
          <p>多企业 AI 可见度运营 · 生美行业版</p>
        </div>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="your@company.com" size="large" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password :prefix-icon="Lock" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="handleLogin">登录</el-button>
      </el-form>
      <div class="footer-tip">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  email: '',
  password: '',
})

const rules: FormRules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.login(form.email, form.password)
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/outcomes'
    router.push(redirect)
  } catch (e: any) {
    // request 拦截器对 401 会 reject(new Error('Unauthorized'))，不一定保留 response
    if (e?.response?.status === 401 || e?.message === 'Unauthorized') {
      ElMessage.error('邮箱或密码错误')
    } else {
      ElMessage.error('网络错误，请稍后重试')
    }
  } finally {
    loading.value = false
  }
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
  max-width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 36px 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
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
  a {
    color: #409eff;
    font-weight: 500;
  }
}
</style>
