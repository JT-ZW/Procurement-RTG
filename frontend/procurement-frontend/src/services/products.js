// Products API services
import apiClient from './api.js'

export const productsAPI = {
  // Get all products
  async getProducts(params = {}) {
    const response = await apiClient.get('/api/v1/products/', { params })
    return response.data
  },

  // Get product by ID
  async getProduct(productId) {
    const response = await apiClient.get(`/api/v1/products/${productId}`)
    return response.data
  },

  // Create new product
  async createProduct(productData) {
    const response = await apiClient.post('/api/v1/products/', productData)
    return response.data
  },

  // Update product
  async updateProduct(productId, productData) {
    const response = await apiClient.put(`/api/v1/products/${productId}`, productData)
    return response.data
  },

  // Delete product
  async deleteProduct(productId) {
    const response = await apiClient.delete(`/api/v1/products/${productId}`)
    return response.data
  }
}
