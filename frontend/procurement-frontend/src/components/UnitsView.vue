<template>
  <div class="units-view">
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pb-2 mb-3 border-bottom">
      <h1 class="h2">Units Management</h1>
      <div class="btn-toolbar mb-2 mb-md-0">
        <button
          type="button"
          class="btn btn-primary"
          @click="openCreateModal"
        >
          <i class="bi bi-plus-circle me-2"></i>
          Add Unit
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="row mb-3">
      <div class="col-md-6">
        <div class="input-group">
          <span class="input-group-text">
            <i class="bi bi-search"></i>
          </span>
          <input
            type="text"
            class="form-control"
            placeholder="Search units..."
            v-model="searchQuery"
            @input="loadUnits"
          >
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- Units Table -->
    <div v-else class="card">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Status</th>
                <th>Created Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="units.length === 0">
                <td colspan="5" class="text-center py-4 text-muted">
                  No units found
                </td>
              </tr>
              <tr v-for="unit in units" :key="unit.id">
                <td>
                  <strong>{{ unit.name }}</strong>
                </td>
                <td>{{ unit.description || '-' }}</td>
                <td>
                  <span
                    class="badge"
                    :class="unit.is_active ? 'bg-success' : 'bg-danger'"
                  >
                    {{ unit.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>{{ formatDate(unit.created_at) }}</td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <button
                      class="btn btn-outline-primary"
                      @click="openEditModal(unit)"
                      title="Edit"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button
                      class="btn btn-outline-danger"
                      @click="confirmDelete(unit)"
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

    <!-- Unit Modal -->
    <div class="modal fade" id="unitModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editingUnit ? 'Edit Unit' : 'Add Unit' }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="saveUnit">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input
                  type="text"
                  class="form-control"
                  v-model="unitForm.name"
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
                  v-model="unitForm.description"
                  :class="{ 'is-invalid': errors.description }"
                ></textarea>
                <div v-if="errors.description" class="invalid-feedback">
                  {{ errors.description }}
                </div>
              </div>

              <div class="mb-3">
                <div class="form-check">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    v-model="unitForm.is_active"
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
                {{ editingUnit ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { unitsAPI } from '@/services/units.js'
import { Modal } from 'bootstrap'

export default {
  name: 'UnitsView',
  setup() {
    const units = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const searchQuery = ref('')

    const editingUnit = ref(null)
    const unitForm = ref({
      name: '',
      description: '',
      is_active: true
    })
    const errors = ref({})

    let unitModal = null

    const loadUnits = async () => {
      loading.value = true
      try {
        const params = {}
        if (searchQuery.value) params.search = searchQuery.value

        const response = await unitsAPI.getUnits(params)
        units.value = response
      } catch (error) {
        console.error('Error loading units:', error)
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingUnit.value = null
      unitForm.value = {
        name: '',
        description: '',
        is_active: true
      }
      errors.value = {}
      unitModal.show()
    }

    const openEditModal = (unit) => {
      editingUnit.value = unit
      unitForm.value = {
        name: unit.name,
        description: unit.description || '',
        is_active: unit.is_active
      }
      errors.value = {}
      unitModal.show()
    }

    const validateForm = () => {
      errors.value = {}

      if (!unitForm.value.name.trim()) {
        errors.value.name = 'Name is required'
      }

      return Object.keys(errors.value).length === 0
    }

    const saveUnit = async () => {
      if (!validateForm()) return

      saving.value = true
      try {
        if (editingUnit.value) {
          await unitsAPI.updateUnit(editingUnit.value.id, unitForm.value)
        } else {
          await unitsAPI.createUnit(unitForm.value)
        }

        unitModal.hide()
        await loadUnits()
      } catch (error) {
        console.error('Error saving unit:', error)
        // Handle validation errors from backend
        if (error.response?.data?.detail) {
          errors.value.general = error.response.data.detail
        }
      } finally {
        saving.value = false
      }
    }

    const confirmDelete = (unit) => {
      if (confirm(`Are you sure you want to delete "${unit.name}"?`)) {
        deleteUnit(unit.id)
      }
    }

    const deleteUnit = async (unitId) => {
      try {
        await unitsAPI.deleteUnit(unitId)
        await loadUnits()
      } catch (error) {
        console.error('Error deleting unit:', error)
        alert('Error deleting unit. Please try again.')
      }
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    onMounted(() => {
      loadUnits()
      // Initialize Bootstrap modal
      const modalEl = document.getElementById('unitModal')
      unitModal = new Modal(modalEl)
    })

    return {
      units,
      loading,
      saving,
      searchQuery,
      editingUnit,
      unitForm,
      errors,
      loadUnits,
      openCreateModal,
      openEditModal,
      saveUnit,
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
