<template>
  <div class="login-container">
    <!-- Animated background elements -->
    <div class="background-pattern"></div>
    <div class="floating-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
      <div class="shape shape-4"></div>
    </div>

    <div class="container-fluid">
      <div class="row justify-content-center align-items-center min-vh-100">
        <div class="col-12 col-sm-10 col-md-8 col-lg-5 col-xl-4">
          <div class="login-card">
            <!-- Header with enhanced branding -->
            <div class="card-header">
              <div class="brand-section">
                <div class="logo-container">
                  <div class="logo-icon-wrapper">
                    <i class="bi bi-building-fill-gear logo-icon"></i>
                    <div class="logo-accent"></div>
                  </div>
                </div>
                <div class="brand-text">
                  <h1 class="brand-title">Rainbow Tourism Group</h1>
                  <p class="brand-subtitle">Procurement Management System</p>
                  <div class="brand-divider"></div>
                </div>
              </div>
            </div>

            <!-- Login form body -->
            <div class="card-body">
              <div class="welcome-section">
                <h2 class="welcome-title">Welcome Back</h2>
                <p class="welcome-subtitle">Sign in to access your procurement dashboard</p>
              </div>

              <form @submit.prevent="handleLogin" class="login-form">
                <!-- Email field -->
                <div class="form-group">
                  <div class="form-floating">
                    <input
                      type="email"
                      class="form-control"
                      id="email"
                      placeholder="name@example.com"
                      v-model="form.email"
                      :class="{ 'is-invalid': errors.email }"
                      required
                    >
                    <label for="email">
                      <i class="bi bi-envelope me-2"></i>Email Address
                    </label>
                    <div v-if="errors.email" class="invalid-feedback">
                      {{ errors.email }}
                    </div>
                  </div>
                </div>

                <!-- Password field -->
                <div class="form-group">
                  <div class="form-floating">
                    <input
                      type="password"
                      class="form-control"
                      id="password"
                      placeholder="Password"
                      v-model="form.password"
                      :class="{ 'is-invalid': errors.password }"
                      required
                    >
                    <label for="password">
                      <i class="bi bi-shield-lock me-2"></i>Password
                    </label>
                    <div v-if="errors.password" class="invalid-feedback">
                      {{ errors.password }}
                    </div>
                  </div>
                </div>

                <!-- Remember me checkbox -->
                <div class="form-group-check">
                  <div class="custom-checkbox">
                    <input
                      type="checkbox"
                      class="form-check-input"
                      id="remember"
                      v-model="form.remember"
                    >
                    <label class="form-check-label" for="remember">
                      <span class="checkmark"></span>
                      Remember me for 30 days
                    </label>
                  </div>
                </div>

                <!-- Error alert -->
                <div class="alert alert-danger alert-custom" v-if="authError" role="alert">
                  <div class="alert-content">
                    <i class="bi bi-exclamation-triangle-fill alert-icon"></i>
                    <div class="alert-text">
                      <strong>Authentication Failed</strong>
                      <p>{{ authError }}</p>
                    </div>
                  </div>
                </div>

                <!-- Submit button -->
                <button
                  type="submit"
                  class="btn btn-primary-enhanced"
                  :disabled="loading"
                >
                  <span v-if="loading" class="btn-loading">
                    <span class="spinner"></span>
                    Signing you in...
                  </span>
                  <span v-else class="btn-content">
                    <i class="bi bi-box-arrow-in-right btn-icon"></i>
                    Sign In Securely
                  </span>
                </button>
              </form>

              <!-- Footer section -->
              <div class="login-footer">
                <div class="divider">
                  <span class="divider-text">New to our system?</span>
                </div>
                <router-link to="/register" class="register-link">
                  <i class="bi bi-person-plus me-2"></i>
                  Create New Account
                </router-link>

                <div class="security-note">
                  <i class="bi bi-shield-check me-2"></i>
                  <span>Secured with enterprise-grade encryption</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    const form = ref({
      email: '',
      password: '',
      remember: false
    })

    const errors = ref({})

    const loading = computed(() => authStore.loading)
    const authError = computed(() => authStore.error)

    const validateForm = () => {
      errors.value = {}

      if (!form.value.email) {
        errors.value.email = 'Email is required'
      } else if (!/\S+@\S+\.\S+/.test(form.value.email)) {
        errors.value.email = 'Email is invalid'
      }

      if (!form.value.password) {
        errors.value.password = 'Password is required'
      } else if (form.value.password.length < 6) {
        errors.value.password = 'Password must be at least 6 characters'
      }

      return Object.keys(errors.value).length === 0
    }

    const handleLogin = async () => {
      if (!validateForm()) return

      try {
        await authStore.login({
          username: form.value.email, // FastAPI expects username field
          password: form.value.password
        })

        router.push({ name: 'Dashboard' })
      } catch (error) {
        console.error('Login error:', error)
      }
    }

    return {
      form,
      errors,
      loading,
      authError,
      handleLogin
    }
  }
}
</script>

<style scoped>
/* Main container with enhanced background */
.login-container {
  background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 25%, #581c87 75%, #7c2d12 100%);
  min-height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 20px;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Animated background pattern */
.background-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 40% 80%, rgba(255, 255, 255, 0.06) 0%, transparent 50%);
  animation: backgroundShift 20s ease-in-out infinite;
}

@keyframes backgroundShift {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(1deg); }
}

/* Floating decorative shapes */
.floating-shapes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  backdrop-filter: blur(10px);
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 10%;
  left: 10%;
  animation: float 15s ease-in-out infinite;
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 70%;
  right: 10%;
  animation: float 20s ease-in-out infinite reverse;
}

.shape-3 {
  width: 60px;
  height: 60px;
  top: 30%;
  right: 20%;
  animation: float 12s ease-in-out infinite;
}

.shape-4 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 20%;
  animation: float 18s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  33% { transform: translateY(-20px) rotate(120deg); }
  66% { transform: translateY(-10px) rotate(240deg); }
}

/* Main login card */
.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  box-shadow:
    0 25px 50px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  overflow: hidden;
  animation: slideInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  max-width: 460px;
  margin: 0 auto;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(60px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Enhanced header */
.card-header {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  color: white;
  padding: 2rem 2rem 1.5rem;
  border: none;
  position: relative;
  overflow: hidden;
}

.card-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #f59e0b, #ef4444, #8b5cf6, #06b6d4);
}

.brand-section {
  text-align: center;
}

.logo-container {
  margin-bottom: 1rem;
}

.logo-icon-wrapper {
  position: relative;
  display: inline-block;
}

.logo-icon {
  font-size: 2.8rem;
  color: #f59e0b;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
  animation: logoGlow 3s ease-in-out infinite;
}

@keyframes logoGlow {
  0%, 100% { filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3)); }
  50% { filter: drop-shadow(0 4px 16px rgba(245, 158, 11, 0.4)); }
}

.logo-accent {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #ef4444, #f59e0b);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

.brand-title {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
  background: linear-gradient(135deg, #ffffff, #e2e8f0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.25px;
}

.brand-divider {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, #f59e0b, #ef4444);
  margin: 0.75rem auto 0;
  border-radius: 2px;
}

/* Welcome section */
.card-body {
  padding: 1.75rem !important;
}

.welcome-section {
  text-align: center;
  margin-bottom: 1.75rem;
}

.welcome-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.welcome-subtitle {
  color: #64748b;
  font-size: 0.95rem;
  margin: 0;
}

/* Form styling */
.login-form {
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-control {
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  padding: 1rem 1.25rem;
  font-size: 1rem;
  background: rgba(248, 250, 252, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.form-control:focus {
  border-color: #3b82f6;
  box-shadow:
    0 0 0 4px rgba(59, 130, 246, 0.1),
    0 4px 6px rgba(0, 0, 0, 0.05);
  background: white;
  transform: translateY(-1px);
}

.form-floating > label {
  color: #6b7280;
  font-weight: 500;
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
}

/* Custom checkbox */
.form-group-check {
  margin-bottom: 1.5rem;
}

.custom-checkbox {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.form-check-input {
  display: none;
}

.checkmark {
  position: relative;
  display: inline-block;
  width: 20px;
  height: 20px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  margin-right: 12px;
  transition: all 0.3s ease;
}

.form-check-input:checked + .form-check-label .checkmark {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-color: #3b82f6;
}

.form-check-input:checked + .form-check-label .checkmark::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.form-check-label {
  color: #4b5563;
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  margin: 0;
}

/* Enhanced button */
.btn-primary-enhanced {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: none;
  border-radius: 16px;
  padding: 1rem 2rem;
  font-weight: 600;
  font-size: 1rem;
  text-transform: none;
  letter-spacing: 0.25px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  width: 100%;
  box-shadow:
    0 4px 6px rgba(59, 130, 246, 0.25),
    0 1px 3px rgba(0, 0, 0, 0.1);
}

.btn-primary-enhanced::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.6s;
}

.btn-primary-enhanced:hover::before {
  left: 100%;
}

.btn-primary-enhanced:hover {
  transform: translateY(-2px);
  box-shadow:
    0 8px 25px rgba(59, 130, 246, 0.4),
    0 4px 6px rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
}

.btn-primary-enhanced:active {
  transform: translateY(0);
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon {
  margin-right: 8px;
  font-size: 1.1rem;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  margin-right: 10px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Enhanced alert */
.alert-custom {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fca5a5;
  border-radius: 12px;
  color: #dc2626;
  font-weight: 500;
  padding: 0.75rem;
  margin-bottom: 1.25rem;
}

.alert-content {
  display: flex;
  align-items: flex-start;
}

.alert-icon {
  font-size: 1.25rem;
  margin-right: 12px;
  margin-top: 2px;
  flex-shrink: 0;
}

.alert-text strong {
  display: block;
  margin-bottom: 4px;
  font-weight: 600;
}

.alert-text p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.9;
}

/* Footer section */
.login-footer {
  text-align: center;
  margin-top: 1rem;
}

.divider {
  position: relative;
  margin: 1.25rem 0 1rem;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
}

.divider-text {
  background: white;
  color: #6b7280;
  padding: 0 1rem;
  font-size: 0.9rem;
  position: relative;
}

.register-link {
  display: inline-flex;
  align-items: center;
  color: #3b82f6;
  text-decoration: none;
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  transition: all 0.3s ease;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.1);
}

.register-link:hover {
  color: #1d4ed8;
  background: rgba(59, 130, 246, 0.1);
  transform: translateY(-1px);
}

.security-note {
  margin-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-size: 0.85rem;
}

/* Responsive design */
@media (max-width: 768px) {
  .login-container {
    padding: 10px;
  }

  .card-header {
    padding: 2rem 1.5rem 1.5rem;
  }

  .card-body {
    padding: 2rem 1.5rem !important;
  }

  .brand-title {
    font-size: 1.75rem;
  }

  .logo-icon {
    font-size: 3rem;
  }

  .welcome-title {
    font-size: 1.25rem;
  }
}

@media (max-width: 480px) {
  .brand-title {
    font-size: 1.5rem;
  }

  .logo-icon {
    font-size: 2.5rem;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .login-card {
    background: rgba(30, 41, 59, 0.95);
    color: #e2e8f0;
  }

  .welcome-title {
    color: #f1f5f9;
  }

  .form-control {
    background: rgba(51, 65, 85, 0.8);
    border-color: #475569;
    color: #e2e8f0;
  }

  .form-control:focus {
    background: rgba(51, 65, 85, 0.9);
  }
}
</style>
