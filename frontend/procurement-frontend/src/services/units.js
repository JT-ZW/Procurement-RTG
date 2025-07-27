// Units API services
import apiClient from './api.js'

export const unitsAPI = {
  // Get all units
  async getUnits(params = {}) {
    const response = await apiClient.get('/api/v1/units/', { params })
    return response.data
  },

  // Get unit by ID
  async getUnit(unitId) {
    const response = await apiClient.get(`/api/v1/units/${unitId}`)
    return response.data
  },

  // Create new unit
  async createUnit(unitData) {
    const response = await apiClient.post('/api/v1/units/', unitData)
    return response.data
  },

  // Update unit
  async updateUnit(unitId, unitData) {
    const response = await apiClient.put(`/api/v1/units/${unitId}`, unitData)
    return response.data
  },

  // Delete unit
  async deleteUnit(unitId) {
    const response = await apiClient.delete(`/api/v1/units/${unitId}`)
    return response.data
  }
}
