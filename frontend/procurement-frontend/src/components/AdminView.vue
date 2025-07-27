<template>
  <div class="admin-view">
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pb-2 mb-3 border-bottom">
      <h1 class="h2">User Management</h1>
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
            placeholder="Search users..."
            v-model="searchQuery"
            @input="loadUsers"
          >
        </div>
      </div>
      <div class="col-md-3">
        <select class="form-select" v-model="roleFilter" @change="loadUsers">
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="user">User</option>
          <option value="viewer">Viewer</option>
        </select>
      </div>
      <div class="col-md-3">
        <select class="form-select" v-model="statusFilter" @change="loadUsers">
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

    <!-- Users Table -->
    <div v-else class="card">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="users.length === 0">
                <td colspan="6" class="text-center py-4 text-muted">
                  No users found
                </td>
              </tr>
              <tr v-for="user in users" :key="user.id">
                <td>
                  <div>
                    <strong>{{ user.first_name }} {{ user.last_name }}</strong>
                    <br>
                    <small class="text-muted">ID: {{ user.id }}</small>
                  </div>
                </td>
                <td>{{ user.email }}</td>
                <td>
                  <span
                    class="badge"
                    :class="getRoleBadgeClass(user.role)"
                  >
                    {{ user.role }}
                  </span>
                </td>
                <td>
                  <span
                    class="badge"
                    :class="user.is_active ? 'bg-success' : 'bg-danger'"
                  >
                    {{ user.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <button
                      class="btn btn-outline-primary"
                      @click="openRoleModal(user)"
                      title="Change Role"
                    >
                      <i class="bi bi-person-gear"></i>
                    </button>
                    <button
                      class="btn"
                      :class="user.is_active ? 'btn-outline-warning' : 'btn-outline-success'"
                      @click="toggleUserStatus(user)"
                      :title="user.is_active ? 'Deactivate' : 'Activate'"
                    >
                      <i :class="user.is_active ? 'bi bi-person-x' : 'bi bi-person-check'"></i>
                    </button>
                    <button
                      class="btn btn-outline-danger"
                      @click="confirmDelete(user)"
                      title="Delete"
                      :disabled="user.id === currentUserId"
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

    <!-- Role Change Modal -->
    <div class="modal fade" id="roleModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Change User Role</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="updateUserRole">
            <div class="modal-body">
              <div v-if="selectedUser">
                <p>
                  <strong>User:</strong> {{ selectedUser.first_name }} {{ selectedUser.last_name }}
                  <br>
                  <strong>Email:</strong> {{ selectedUser.email }}
                  <br>
                  <strong>Current Role:</strong>
                  <span
                    class="badge ms-1"
                    :class="getRoleBadgeClass(selectedUser.role)"
                  >
                    {{ selectedUser.role }}
                  </span>
                </p>
              </div>

              <div class="mb-3">
                <label class="form-label">New Role</label>
                <select
                  class="form-select"
                  v-model="newRole"
                  required
                >
                  <option value="">Select Role</option>
                  <option value="admin">Admin</option>
                  <option value="user">User</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>

              <div class="alert alert-info">
                <strong>Role Permissions:</strong>
                <ul class="mb-0 mt-2">
                  <li><strong>Admin:</strong> Full system access, manage units and users</li>
                  <li><strong>User:</strong> Manage products within assigned unit</li>
                  <li><strong>Viewer:</strong> Read-only access to products</li>
                </ul>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
                Update Role
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
import { adminAPI } from '@/services/admin.js'
import { Modal } from 'bootstrap'

export default {
  name: 'AdminView',
  setup() {
    const authStore = useAuthStore()

    const users = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const searchQuery = ref('')
    const roleFilter = ref('')
    const statusFilter = ref('')

    const selectedUser = ref(null)
    const newRole = ref('')

    const currentUserId = computed(() => authStore.user?.id)

    let roleModal = null

    const loadUsers = async () => {
      loading.value = true
      try {
        const params = {}
        if (searchQuery.value) params.search = searchQuery.value
        if (roleFilter.value) params.role = roleFilter.value
        if (statusFilter.value) params.is_active = statusFilter.value === 'active'

        const response = await adminAPI.getUsers(params)
        users.value = response
      } catch (error) {
        console.error('Error loading users:', error)
      } finally {
        loading.value = false
      }
    }

    const getRoleBadgeClass = (role) => {
      switch (role) {
        case 'admin': return 'bg-danger'
        case 'user': return 'bg-primary'
        case 'viewer': return 'bg-secondary'
        default: return 'bg-light'
      }
    }

    const openRoleModal = (user) => {
      selectedUser.value = user
      newRole.value = user.role
      roleModal.show()
    }

    const updateUserRole = async () => {
      if (!selectedUser.value || !newRole.value) return

      saving.value = true
      try {
        await adminAPI.updateUserRole(selectedUser.value.id, { role: newRole.value })
        roleModal.hide()
        await loadUsers()
      } catch (error) {
        console.error('Error updating user role:', error)
        alert('Error updating user role. Please try again.')
      } finally {
        saving.value = false
      }
    }

    const toggleUserStatus = async (user) => {
      const action = user.is_active ? 'deactivate' : 'activate'
      if (confirm(`Are you sure you want to ${action} "${user.first_name} ${user.last_name}"?`)) {
        try {
          await adminAPI.toggleUserStatus(user.id)
          await loadUsers()
        } catch (error) {
          console.error('Error toggling user status:', error)
          alert('Error updating user status. Please try again.')
        }
      }
    }

    const confirmDelete = (user) => {
      if (user.id === currentUserId.value) {
        alert('You cannot delete your own account.')
        return
      }

      if (confirm(`Are you sure you want to delete "${user.first_name} ${user.last_name}"? This action cannot be undone.`)) {
        deleteUser(user.id)
      }
    }

    const deleteUser = async (userId) => {
      try {
        await adminAPI.deleteUser(userId)
        await loadUsers()
      } catch (error) {
        console.error('Error deleting user:', error)
        alert('Error deleting user. Please try again.')
      }
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    onMounted(() => {
      loadUsers()
      // Initialize Bootstrap modal
      const modalEl = document.getElementById('roleModal')
      roleModal = new Modal(modalEl)
    })

    return {
      users,
      loading,
      saving,
      searchQuery,
      roleFilter,
      statusFilter,
      selectedUser,
      newRole,
      currentUserId,
      loadUsers,
      getRoleBadgeClass,
      openRoleModal,
      updateUserRole,
      toggleUserStatus,
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

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
