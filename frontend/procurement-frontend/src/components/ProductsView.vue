<template>
  <div class="products-view">
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pb-2 mb-3 border-bottom">
      <h1 class="h2">Products</h1>
      <div class="btn-toolbar mb-2 mb-md-0">
        <button
          type="button"
          class="btn btn-primary"
          @click="openCreateModal"
          v-if="!isViewer"
        >
          <i class="bi bi-plus-circle me-2"></i>
          Add Product
        </button>
      </div>
    </div>

    <!-- Search and Filter -->
    <div class="row mb-3">
      <div class="col-md-6">
        <div class="input-group">
          <span class="input-group-text">
            <i class="bi bi-search"></i>
          </span>
          <input
            type="text"
            class="form-control"
            placeholder="Search products..."
            v-model="searchQuery"
            @input="loadProducts"
          >
        </div>
      </div>
      <div class="col-md-3">
        <select class="form-select" v-model="categoryFilter" @change="loadProducts">
          <option value="">All Categories</option>
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </div>
      <div class="col-md-3">
        <select class="form-select" v-model="statusFilter" @change="loadProducts">
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- Products Table -->
    <div v-else class="card">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Price</th>
                <th>Status</th>
                <th>Created Date</th>
                <th v-if="!isViewer">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="products.length === 0">
                <td :colspan="isViewer ? 5 : 6" class="text-center py-4 text-muted">
                  No products found
                </td>
              </tr>
              <tr v-for="product in products" :key="product.id">
                <td>
                  <div>
                    <strong>{{ product.name }}</strong>
                    <br>
                    <small class="text-muted">{{ product.description }}</small>
                  </div>
                </td>
                <td>
                  <span class="badge bg-secondary">{{ product.category }}</span>
                </td>
                <td>
                  <strong>${{ product.price }}</strong>
                </td>
                <td>
                  <span
                    class="badge"
                    :class="product.is_active ? 'bg-success' : 'bg-danger'"
                  >
                    {{ product.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>{{ formatDate(product.created_at) }}</td>
                <td v-if="!isViewer">
                  <div class="btn-group btn-group-sm">
                    <button
                      class="btn btn-outline-primary"
                      @click="openEditModal(product)"
                      title="Edit"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button
                      class="btn btn-outline-danger"
                      @click="confirmDelete(product)"
                      title="Delete"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Product Modal -->
    <div class="modal fade" id="productModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editingProduct ? 'Edit Product' : 'Add Product' }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="saveProduct">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input
                  type="text"
                  class="form-control"
                  v-model="productForm.name"
                  :class="{ 'is-invalid': errors.name }"
                  required
                >
                <div v-if="errors.name" class="invalid-feedback">
                  {{ errors.name }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea
                  class="form-control"
                  rows="3"
                  v-model="productForm.description"
                  :class="{ 'is-invalid': errors.description }"
                ></textarea>
                <div v-if="errors.description" class="invalid-feedback">
                  {{ errors.description }}
                </div>
              </div>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">Code</label>
                    <input
                      type="text"
                      class="form-control"
                      v-model="productForm.code"
                      :class="{ 'is-invalid': errors.code }"
                      required
                    >
                    <div v-if="errors.code" class="invalid-feedback">
                      {{ errors.code }}
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">Unit of Measure</label>
                    <select
                      class="form-control"
                      v-model="productForm.unit_of_measure"
                      :class="{ 'is-invalid': errors.unit_of_measure }"
                    >
                      <option value="pieces">Pieces</option>
                      <option value="kg">Kilograms</option>
                      <option value="liters">Liters</option>
                      <option value="boxes">Boxes</option>
                      <option value="bottles">Bottles</option>
                    </select>
                    <div v-if="errors.unit_of_measure" class="invalid-feedback">
                      {{ errors.unit_of_measure }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">Category ID (Optional)</label>
                    <input
                      type="text"
                      class="form-control"
                      v-model="productForm.category_id"
                      :class="{ 'is-invalid': errors.category_id }"
                      placeholder="Enter category UUID"
                    >
                    <div v-if="errors.category_id" class="invalid-feedback">
                      {{ errors.category_id }}
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">Standard Cost</label>
                    <input
                      type="number"
                      step="0.01"
                      class="form-control"
                      v-model="productForm.standard_cost"
                      :class="{ 'is-invalid': errors.standard_cost }"
                    >
                    <div v-if="errors.standard_cost" class="invalid-feedback">
                      {{ errors.standard_cost }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="row">
                <div class="col-md-4">
                  <div class="mb-3">
                    <label class="form-label">Currency</label>
                    <select
                      class="form-control"
                      v-model="productForm.currency"
                    >
                      <option value="USD">USD</option>
                      <option value="EUR">EUR</option>
                      <option value="GBP">GBP</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="mb-3">
                    <label class="form-label">Min Stock</label>
                    <input
                      type="number"
                      class="form-control"
                      v-model="productForm.minimum_stock_level"
                    >
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="mb-3">
                    <label class="form-label">Max Stock</label>
                    <input
                      type="number"
                      class="form-control"
                      v-model="productForm.maximum_stock_level"
                    >
                  </div>
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Reorder Point</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="productForm.reorder_point"
                >
              </div>

              <div class="mb-3">
                <div class="form-check">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    v-model="productForm.is_active"
                  >
                  <label class="form-check-label">
                    Active
                  </label>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
                {{ editingProduct ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import { productsAPI } from '@/services/products.js'
import { Modal } from 'bootstrap'

export default {
  name: 'ProductsView',
  setup() {
    const authStore = useAuthStore()

    const products = ref([])
    const categories = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const searchQuery = ref('')
    const categoryFilter = ref('')
    const statusFilter = ref('')

    const editingProduct = ref(null)
    const productForm = ref({
      name: '',
      code: '',
      description: '',
      category_id: '',
      unit_of_measure: 'pieces',
      standard_cost: 0,
      currency: 'USD',
      minimum_stock_level: 0,
      maximum_stock_level: 1000,
      reorder_point: 10,
      is_active: true
    })
    const errors = ref({})

    const isViewer = computed(() => authStore.isViewer)

    let productModal = null

    const loadProducts = async () => {
      loading.value = true
      try {
        const params = {}
        if (searchQuery.value) params.search = searchQuery.value
        if (categoryFilter.value) params.category = categoryFilter.value
        if (statusFilter.value) params.is_active = statusFilter.value === 'active'

        const response = await productsAPI.getProducts(params)
        products.value = response

        // Extract unique categories
        const uniqueCategories = [...new Set(response.map(p => p.category))]
        categories.value = uniqueCategories.filter(Boolean)
      } catch (error) {
        console.error('Error loading products:', error)
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingProduct.value = null
      productForm.value = {
        name: '',
        description: '',
        category: '',
        price: 0,
        is_active: true
      }
      errors.value = {}
      productModal.show()
    }

    const openEditModal = (product) => {
      editingProduct.value = product
      productForm.value = {
        name: product.name,
        description: product.description || '',
        category: product.category,
        price: product.price,
        is_active: product.is_active
      }
      errors.value = {}
      productModal.show()
    }

    const validateForm = () => {
      errors.value = {}

      if (!productForm.value.name.trim()) {
        errors.value.name = 'Name is required'
      }

      if (!productForm.value.category.trim()) {
        errors.value.category = 'Category is required'
      }

      if (!productForm.value.price || productForm.value.price < 0) {
        errors.value.price = 'Valid price is required'
      }

      return Object.keys(errors.value).length === 0
    }

    const saveProduct = async () => {
      if (!validateForm()) return

      saving.value = true
      try {
        const productData = {
          ...productForm.value,
          price: parseFloat(productForm.value.price)
        }

        if (editingProduct.value) {
          await productsAPI.updateProduct(editingProduct.value.id, productData)
        } else {
          await productsAPI.createProduct(productData)
        }

        productModal.hide()
        await loadProducts()
      } catch (error) {
        console.error('Error saving product:', error)
        // Handle validation errors from backend
        if (error.response?.data?.detail) {
          errors.value.general = error.response.data.detail
        }
      } finally {
        saving.value = false
      }
    }

    const confirmDelete = (product) => {
      if (confirm(`Are you sure you want to delete "${product.name}"?`)) {
        deleteProduct(product.id)
      }
    }

    const deleteProduct = async (productId) => {
      try {
        await productsAPI.deleteProduct(productId)
        await loadProducts()
      } catch (error) {
        console.error('Error deleting product:', error)
        alert('Error deleting product. Please try again.')
      }
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    onMounted(() => {
      loadProducts()
      // Initialize Bootstrap modal
      const modalEl = document.getElementById('productModal')
      productModal = new Modal(modalEl)
    })

    return {
      products,
      categories,
      loading,
      saving,
      searchQuery,
      categoryFilter,
      statusFilter,
      editingProduct,
      productForm,
      errors,
      isViewer,
      loadProducts,
      openCreateModal,
      openEditModal,
      saveProduct,
      confirmDelete,
      formatDate
    }
  }
}
</script>

<style scoped>
.table th {
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
}

.badge {
  font-size: 0.75em;
}

.btn-group-sm > .btn {
  padding: 0.25rem 0.5rem;
}

.input-group-text {
  background-color: #f8f9fa;
  border-right: none;
}

.input-group .form-control {
  border-left: none;
}

.input-group .form-control:focus {
  border-left: none;
  box-shadow: none;
}

.card {
  border: none;
  box-shadow: 0 2px 4px rgba(0,0,0,.1);
}
</style>
