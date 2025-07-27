<template>
  <div id="app">
    <div v-if="loading" class="d-flex justify-content-center align-items-center" style="min-height: 100vh;">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <router-view v-else />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'App',
  setup() {
    const authStore = useAuthStore()
    const loading = ref(true)

    onMounted(async () => {
      try {
        // Initialize auth state on app startup
        await authStore.initAuth()
      } catch (error) {
        console.error('Auth initialization error:', error)
      } finally {
        loading.value = false
      }
    })

    return {
      loading
    }
  }
}
</script>

<style>
/* Reset and Bootstrap overrides */
*, *::before, *::after {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f8f9fa;
}

#app {
  min-height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

/* Ensure Bootstrap containers work properly */
.container, .container-fluid {
  width: 100%;
  max-width: 100%;
}

.row {
  margin-left: -15px;
  margin-right: -15px;
}

[class*="col-"] {
  padding-left: 15px;
  padding-right: 15px;
}
</style>
