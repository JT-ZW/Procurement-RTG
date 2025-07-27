// Admin API services
import apiClient from './api.js'

export const adminAPI = {
  // Get admin dashboard stats
  async getDashboardStats() {
    const response = await apiClient.get('/api/v1/admin/dashboard-stats')
    return response.data
  },

  // Get all users (admin only)
  async getUsers(params = {}) {
    const response = await apiClient.get('/api/v1/users/', { params })
    return response.data
  },

  // Get user by ID
  async getUser(userId) {
    const response = await apiClient.get(`/api/v1/users/${userId}`)
    return response.data
  },

  // Update user role
  async updateUserRole(userId, roleData) {
    const response = await apiClient.put(`/api/v1/users/${userId}/role`, roleData)
    return response.data
  },

  // Toggle user active status
  async toggleUserStatus(userId) {
    const response = await apiClient.put(`/api/v1/users/${userId}/toggle-status`)
    return response.data
  },

  // Delete user
  async deleteUser(userId) {
    const response = await apiClient.delete(`/api/v1/users/${userId}`)
    return response.data
  }
}
