<template>
  <div class="register-container">
    <div class="background-overlay"></div>
    <div class="container-fluid">
      <div class="row justify-content-center align-items-center min-vh-100">
        <div class="col-12 col-sm-10 col-md-8 col-lg-6 col-xl-5">
          <div class="register-card">
            <div class="card-header text-center">
              <div class="logo-container">
                <i class="bi bi-building-fill-gear logo-icon"></i>
              </div>
              <h2 class="brand-title">Join Gateway Stream</h2>
              <p class="brand-subtitle">Create your procurement account</p>
            </div>

            <div class="card-body">
              <form @submit.prevent="handleRegister">
                <div class="row">
                  <div class="col-md-6">
                    <div class="form-floating mb-3">
                      <input
                        type="text"
                        class="form-control"
                        id="firstName"
                        placeholder="First Name"
                        v-model="form.first_name"
                        :class="{ 'is-invalid': errors.first_name }"
                        required
                      >
                      <label for="firstName">First Name</label>
                      <div v-if="errors.first_name" class="invalid-feedback">
                        {{ errors.first_name }}
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="form-floating mb-3">
                      <input
                        type="text"
                        class="form-control"
                        id="lastName"
                        placeholder="Last Name"
                        v-model="form.last_name"
                        :class="{ 'is-invalid': errors.last_name }"
                        required
                      >
                      <label for="lastName">Last Name</label>
                      <div v-if="errors.last_name" class="invalid-feedback">
                        {{ errors.last_name }}
                      </div>
                    </div>
                  </div>
                </div>

                <div class="form-floating mb-3">
                  <input
                    type="email"
                    class="form-control"
                    id="email"
                    placeholder="name@example.com"
                    v-model="form.email"
                    :class="{ 'is-invalid': errors.email }"
                    required
                  >
                  <label for="email">Email Address</label>
                  <div v-if="errors.email" class="invalid-feedback">
                    {{ errors.email }}
                  </div>
                </div>

                <div class="form-floating mb-3">
                  <input
                    type="password"
                    class="form-control"
                    id="password"
                    placeholder="Password"
                    v-model="form.password"
                    :class="{ 'is-invalid': errors.password }"
                    required
                  >
                  <label for="password">Password</label>
                  <div v-if="errors.password" class="invalid-feedback">
                    {{ errors.password }}
                  </div>
                </div>

                <div class="form-floating mb-4">
                  <input
                    type="password"
                    class="form-control"
                    id="confirmPassword"
                    placeholder="Confirm Password"
                    v-model="form.confirmPassword"
                    :class="{ 'is-invalid': errors.confirmPassword }"
                    required
                  >
                  <label for="confirmPassword">Confirm Password</label>
                  <div v-if="errors.confirmPassword" class="invalid-feedback">
                    {{ errors.confirmPassword }}
                  </div>
                </div>

                <div class="alert alert-danger alert-custom" v-if="authError" role="alert">
                  <i class="bi bi-exclamation-triangle-fill me-2"></i>
                  {{ authError }}
                </div>

                <div class="alert alert-success alert-success-custom" v-if="successMessage" role="alert">
                  <i class="bi bi-check-circle-fill me-2"></i>
                  {{ successMessage }}
                </div>

                <button
                  type="submit"
                  class="btn btn-primary-custom w-100 mb-3"
                  :disabled="loading"
                >
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
                  <span v-if="!loading"><i class="bi bi-person-plus-fill me-2"></i></span>
                  {{ loading ? 'Creating Account...' : 'Create Account' }}
                </button>
              </form>

              <div class="text-center">
                <p class="login-link">
                  Already have an account?
                  <router-link to="/login" class="link-custom">
                    Sign In Here
                  </router-link>
                </p>
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
  name: 'RegisterView',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    const form = ref({
      first_name: '',
      last_name: '',
      email: '',
      password: '',
      confirmPassword: ''
    })

    const errors = ref({})
    const successMessage = ref('')

    const loading = computed(() => authStore.loading)
    const authError = computed(() => authStore.error)

    const validateForm = () => {
      errors.value = {}

      if (!form.value.first_name) {
        errors.value.first_name = 'First name is required'
      }

      if (!form.value.last_name) {
        errors.value.last_name = 'Last name is required'
      }

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

      if (!form.value.confirmPassword) {
        errors.value.confirmPassword = 'Please confirm your password'
      } else if (form.value.password !== form.value.confirmPassword) {
        errors.value.confirmPassword = 'Passwords do not match'
      }

      return Object.keys(errors.value).length === 0
    }

    const handleRegister = async () => {
      if (!validateForm()) return

      try {
        // eslint-disable-next-line no-unused-vars
        const { confirmPassword, ...registerData } = form.value
        await authStore.register(registerData)

        successMessage.value = 'Account created successfully! You can now sign in.'

        // Clear form
        form.value = {
          first_name: '',
          last_name: '',
          email: '',
          password: '',
          confirmPassword: ''
        }

        // Redirect to login after 2 seconds
        setTimeout(() => {
          router.push({ name: 'Login' })
        }, 2000)

      } catch (error) {
        console.error('Registration error:', error)
      }
    }

    return {
      form,
      errors,
      loading,
      authError,
      successMessage,
      handleRegister
    }
  }
}
</script>

<style scoped>
.register-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 20px 0;
  position: relative;
  overflow: hidden;
}

.background-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  opacity: 0.3;
}

.min-vh-100 {
  min-height: 100vh !important;
  position: relative;
  z-index: 1;
}

.register-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-header {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  color: white;
  padding: 2.5rem 2rem 2rem;
  border: none;
}

.logo-container {
  margin-bottom: 1rem;
}

.logo-icon {
  font-size: 3rem;
  color: #f39c12;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

.brand-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.brand-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  margin: 0;
  font-weight: 300;
}

.card-body {
  padding: 2.5rem !important;
}

.form-floating {
  margin-bottom: 1.5rem;
}

.form-control {
  border: 2px solid #e8ecf0;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  font-size: 1rem;
  background: rgba(248, 249, 250, 0.8);
  transition: all 0.3s ease;
  height: auto;
}

.form-control:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.15);
  background: white;
  transform: translateY(-1px);
}

.form-floating > label {
  color: #6c757d;
  font-weight: 500;
  padding: 1rem 1.25rem;
}

.btn-primary-custom {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  font-weight: 600;
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.btn-primary-custom::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}

.btn-primary-custom:hover::before {
  left: 100%;
}

.btn-primary-custom:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
}

.btn-primary-custom:active {
  transform: translateY(0);
}

.alert-custom {
  background: linear-gradient(135deg, #fc8181 0%, #f56565 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-weight: 500;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.alert-success-custom {
  background: linear-gradient(135deg, #68d391 0%, #48bb78 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-weight: 500;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.login-link {
  color: #6c757d;
  font-weight: 500;
  margin: 0;
}

.link-custom {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
}

.link-custom:hover {
  color: #5a67d8;
  text-decoration: underline;
}

/* Input field enhancements */
.form-control:invalid {
  border-color: #e74c3c;
}

.form-control:valid {
  border-color: #27ae60;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .register-container {
    padding: 10px 0;
  }

  .card-header {
    padding: 2rem 1.5rem 1.5rem;
  }

  .card-body {
    padding: 2rem 1.5rem !important;
  }

  .brand-title {
    font-size: 1.5rem;
  }

  .logo-icon {
    font-size: 2.5rem;
  }

  .form-floating {
    margin-bottom: 1rem;
  }
}

@media (max-width: 576px) {
  .register-container {
    padding: 5px 0;
  }

  .card-header {
    padding: 1.5rem 1rem 1rem;
  }

  .card-body {
    padding: 1.5rem 1rem !important;
  }

  .brand-title {
    font-size: 1.3rem;
  }

  .brand-subtitle {
    font-size: 0.8rem;
  }
}

/* Premium touches */
.register-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #f39c12, #e74c3c, #9b59b6, #3498db, #1abc9c, #f39c12);
  background-size: 200% 100%;
  animation: shimmer 3s linear infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>
