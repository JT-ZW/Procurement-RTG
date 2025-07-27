import { defineStore } from 'pinia'
import { authAPI } from '@/services/auth.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token'),
    currentUnit: localStorage.getItem('current_unit_id'),
    isAuthenticated: false,
    loading: false,
    error: null
  }),

  getters: {
    isAdmin: (state) => state.user?.role === 'admin' || state.user?.role === 'superuser',
    isViewer: (state) => state.user?.role === 'viewer',
    isUser: (state) => state.user?.role === 'user',
    userName: (state) => state.user ? `${state.user.first_name} ${state.user.last_name}` : '',
    userEmail: (state) => state.user?.email || ''
  },

  actions: {
    async login(credentials) {
      this.loading = true
      this.error = null

      try {
        const response = await authAPI.login(credentials)
        this.token = response.access_token
        this.user = response.user
        this.isAuthenticated = true

        // Store token in localStorage
        localStorage.setItem('access_token', response.access_token)

        return response
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed'
        throw error
      } finally {
        this.loading = false
      }
    },

    async register(userData) {
      this.loading = true
      this.error = null

      try {
        const response = await authAPI.register(userData)
        return response
      } catch (error) {
        this.error = error.response?.data?.detail || 'Registration failed'
        throw error
      } finally {
        this.loading = false
      }
    },

    async logout() {
      try {
        await authAPI.logout()
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.clearAuth()
      }
    },

    async getCurrentUser() {
      if (!this.token) return

      try {
        const user = await authAPI.getCurrentUser()
        this.user = user
        this.isAuthenticated = true
      } catch (error) {
        this.clearAuth()
        throw error
      }
    },

    clearAuth() {
      this.user = null
      this.token = null
      this.currentUnit = null
      this.isAuthenticated = false
      this.error = null

      localStorage.removeItem('access_token')
      localStorage.removeItem('current_unit_id')
    },

    setCurrentUnit(unitId) {
      this.currentUnit = unitId
      localStorage.setItem('current_unit_id', unitId)
    },

    async refreshToken() {
      try {
        const response = await authAPI.refreshToken()
        this.token = response.access_token
        localStorage.setItem('access_token', response.access_token)
        return response
      } catch (error) {
        this.clearAuth()
        throw error
      }
    },

    // Initialize auth state on app startup
    async initAuth() {
      if (this.token) {
        try {
          await this.getCurrentUser()
        } catch (error) {
          this.clearAuth()
        }
      }
    }
  }
})
