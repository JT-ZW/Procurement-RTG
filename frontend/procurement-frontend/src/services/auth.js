// Authentication API services
import apiClient from './api.js'

export const authAPI = {
  // Register new user
  async register(userData) {
    const response = await apiClient.post('/auth/register/json', {
      email: userData.email,
      password: userData.password,
      name: userData.name,
      unit: userData.unit || 'main'
    })
    return response.data
  },

  // Login user
  async login(credentials) {
    const response = await apiClient.post('/auth/login/json', {
      email: credentials.email || credentials.username,
      password: credentials.password
    })
    return response.data
  },

  // Refresh token
  async refreshToken() {
    // Not implemented in current backend
    throw new Error('Refresh token not implemented yet')
  },

  // Logout
  async logout() {
    // Simple logout - just clear local storage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('current_unit_id')
    return { message: 'Logged out successfully' }
  },

  // Get current user info
  async getCurrentUser() {
    const response = await apiClient.get('/auth/me')
    return response.data
  }
}
