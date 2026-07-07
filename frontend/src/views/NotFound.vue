<template>
  <el-result icon="warning" title="404" sub-title="页面不存在或已被移动">
    <template #extra>
      <router-link to="/outcomes">
        <el-button type="primary">返回首页</el-button>
      </router-link>
    </template>
  </el-result>
</template>
