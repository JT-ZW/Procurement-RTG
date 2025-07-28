<template>
  <div class="dashboard">
    <!-- Navigation Header -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">
          <i class="bi bi-basket2-fill me-2"></i>
          Procurement System
        </a>

        <div class="navbar-nav ms-auto">
          <div class="nav-item dropdown">
            <a
              class="nav-link dropdown-toggle d-flex align-items-center"
              href="#"
              role="button"
              data-bs-toggle="dropdown"
            >
              <i class="bi bi-person-circle me-2"></i>
              {{ userName }}
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><span class="dropdown-item-text">{{ userEmail }}</span></li>
              <li><hr class="dropdown-divider"></li>
              <li>
                <a class="dropdown-item" href="#" @click="handleLogout">
                  <i class="bi bi-box-arrow-right me-2"></i>
                  Logout
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </nav>

    <div class="container-fluid">
      <div class="row">
        <!-- Sidebar -->
        <nav class="col-md-3 col-lg-2 d-md-block bg-light sidebar">
          <div class="position-sticky pt-3">
            <!-- Unit Selector -->
            <div class="mb-3" v-if="!isAdmin">
              <label class="form-label small text-muted">Current Unit</label>
              <select
                class="form-select form-select-sm"
                v-model="selectedUnit"
                @change="handleUnitChange"
              >
                <option value="">Select Unit</option>
                <option
                  v-for="unit in units"
                  :key="unit.id"
                  :value="unit.id"
                >
                  {{ unit.name }}
                </option>
              </select>
            </div>

            <ul class="nav flex-column">
              <li class="nav-item">
                <a
                  class="nav-link"
                  :class="{ active: activeTab === 'dashboard' }"
                  href="#"
                  @click="setActiveTab('dashboard')"
                >
                  <i class="bi bi-speedometer2 me-2"></i>
                  Dashboard
                </a>
              </li>

              <li class="nav-item" v-if="!isViewer">
                <a
                  class="nav-link"
                  :class="{ active: activeTab === 'products' }"
                  href="#"
                  @click="setActiveTab('products')"
                >
                  <i class="bi bi-box-seam me-2"></i>
                  Products
                </a>
              </li>

              <li class="nav-item" v-if="!isViewer">
                <a
                  class="nav-link"
                  :class="{ active: activeTab === 'suppliers' }"
                  href="#"
                  @click="setActiveTab('suppliers')"
                >
                  <i class="bi bi-truck me-2"></i>
                  Suppliers
                </a>
              </li>

              <li class="nav-item" v-if="!isViewer">
                <a
                  class="nav-link"
                  :class="{ active: activeTab === 'requisitions' }"
                  href="#"
                  @click="setActiveTab('requisitions')"
                >
                  <i class="bi bi-clipboard-check me-2"></i>
                  Purchase Requisitions
                </a>
              </li>

              <li class="nav-item" v-if="isAdmin">
                <a
                  class="nav-link"
                  :class="{ active: activeTab === 'units' }"
                  href="#"
                  @click="setActiveTab('units')"
                >
                  <i class="bi bi-building me-2"></i>
                  Units
                </a>
              </li>

              <li class="nav-item" v-if="isAdmin">
                <a
                  class="nav-link"
                  :class="{ active: activeTab === 'admin' }"
                  href="#"
                  @click="setActiveTab('admin')"
                >
                  <i class="bi bi-people me-2"></i>
                  Admin
                </a>
              </li>
            </ul>
          </div>
        </nav>

        <!-- Main Content -->
        <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
          <div class="pt-3">
            <!-- Dashboard Tab -->
            <div v-if="activeTab === 'dashboard'">
              <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pb-2 mb-3 border-bottom">
                <h1 class="h2">Dashboard</h1>
              </div>

              <!-- Stats Cards -->
              <div class="row mb-4">
                <div class="col-md-3 mb-3">
                  <div class="card bg-primary text-white">
                    <div class="card-body">
                      <div class="d-flex justify-content-between">
                        <div>
                          <h4 class="mb-0">{{ stats.total_products || 0 }}</h4>
                          <p class="mb-0">Total Products</p>
                        </div>
                        <i class="bi bi-box-seam fs-2"></i>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="col-md-3 mb-3" v-if="isAdmin">
                  <div class="card bg-success text-white">
                    <div class="card-body">
                      <div class="d-flex justify-content-between">
                        <div>
                          <h4 class="mb-0">{{ stats.total_units || 0 }}</h4>
                          <p class="mb-0">Total Units</p>
                        </div>
                        <i class="bi bi-building fs-2"></i>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="col-md-3 mb-3" v-if="isAdmin">
                  <div class="card bg-info text-white">
                    <div class="card-body">
                      <div class="d-flex justify-content-between">
                        <div>
                          <h4 class="mb-0">{{ stats.total_users || 0 }}</h4>
                          <p class="mb-0">Total Users</p>
                        </div>
                        <i class="bi bi-people fs-2"></i>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="col-md-3 mb-3" v-if="isAdmin">
                  <div class="card bg-warning text-white">
                    <div class="card-body">
                      <div class="d-flex justify-content-between">
                        <div>
                          <h4 class="mb-0">{{ stats.active_users || 0 }}</h4>
                          <p class="mb-0">Active Users</p>
                        </div>
                        <i class="bi bi-person-check fs-2"></i>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Welcome Message -->
              <div class="alert alert-info">
                <h5 class="alert-heading">Welcome to the Procurement System!</h5>
                <p class="mb-0">
                  <span v-if="isAdmin">
                    As an administrator, you have full access to manage units, products, and users.
                  </span>
                  <span v-else-if="isViewer">
                    As a viewer, you can browse products and view system information.
                  </span>
                  <span v-else>
                    You can manage products within your assigned unit.
                  </span>
                </p>
              </div>
            </div>

            <!-- Products Tab -->
            <ProductsView v-if="activeTab === 'products'" />

            <!-- Suppliers Tab -->
            <div v-if="activeTab === 'suppliers'">
              <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pb-2 mb-3 border-bottom">
                <h1 class="h2">Suppliers</h1>
                <button class="btn btn-primary" @click="loadSuppliers">
                  <i class="bi bi-arrow-clockwise me-2"></i>
                  Refresh
                </button>
              </div>

              <div class="row">
                <div class="col-12">
                  <div class="table-responsive">
                    <table class="table table-striped">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Code</th>
                          <th>Contact Person</th>
                          <th>Email</th>
                          <th>Phone</th>
                          <th>City</th>
                          <th>Country</th>
                          <th>Rating</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="supplier in suppliers" :key="supplier.id">
                          <td>{{ supplier.name }}</td>
                          <td>{{ supplier.code }}</td>
                          <td>{{ supplier.contact_person }}</td>
                          <td>{{ supplier.email }}</td>
                          <td>{{ supplier.phone }}</td>
                          <td>{{ supplier.city }}</td>
                          <td>{{ supplier.country }}</td>
                          <td>
                            <span class="badge bg-primary">{{ supplier.rating }}/5</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            <!-- Purchase Requisitions Tab -->
            <div v-if="activeTab === 'requisitions'">
              <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pb-2 mb-3 border-bottom">
                <h1 class="h2">Purchase Requisitions</h1>
                <button class="btn btn-primary" @click="loadRequisitions">
                  <i class="bi bi-arrow-clockwise me-2"></i>
                  Refresh
                </button>
              </div>

              <div class="row">
                <div class="col-12">
                  <div class="table-responsive">
                    <table class="table table-striped">
                      <thead>
                        <tr>
                          <th>Requisition #</th>
                          <th>Title</th>
                          <th>Requester</th>
                          <th>Unit</th>
                          <th>Status</th>
                          <th>Priority</th>
                          <th>Amount</th>
                          <th>Requested Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="req in requisitions" :key="req.id">
                          <td>{{ req.requisition_number }}</td>
                          <td>{{ req.title }}</td>
                          <td>{{ req.requester_name }}</td>
                          <td>{{ req.unit_name }}</td>
                          <td>
                            <span class="badge" :class="getStatusBadgeClass(req.status)">
                              {{ req.status }}
                            </span>
                          </td>
                          <td>
                            <span class="badge" :class="getPriorityBadgeClass(req.priority)">
                              {{ req.priority }}
                            </span>
                          </td>
                          <td>${{ req.total_estimated_amount }}</td>
                          <td>{{ formatDate(req.requested_date) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            <!-- Units Tab -->
            <UnitsView v-if="activeTab === 'units' && isAdmin" />

            <!-- Admin Tab -->
            <AdminView v-if="activeTab === 'admin' && isAdmin" />
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { unitsAPI } from '@/services/units.js'
import { adminAPI } from '@/services/admin.js'
import ProductsView from '@/components/ProductsView.vue'
import UnitsView from '@/components/UnitsView.vue'
import AdminView from '@/components/AdminView.vue'

export default {
  name: 'DashboardView',
  components: {
    ProductsView,
    UnitsView,
    AdminView
  },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    const activeTab = ref('dashboard')
    const units = ref([])
    const selectedUnit = ref(authStore.currentUnit)
    const stats = ref({})
    const suppliers = ref([])
    const requisitions = ref([])
    const loading = ref(false)

    const userName = computed(() => authStore.userName)
    const userEmail = computed(() => authStore.userEmail)
    const isAdmin = computed(() => authStore.isAdmin)
    const isViewer = computed(() => authStore.isViewer)

    const setActiveTab = (tab) => {
      activeTab.value = tab
    }

    const handleUnitChange = () => {
      authStore.setCurrentUnit(selectedUnit.value)
      // Refresh data when unit changes
      loadDashboardData()
    }

    const handleLogout = async () => {
      await authStore.logout()
      router.push({ name: 'Login' })
    }

    const loadUnits = async () => {
      try {
        const response = await unitsAPI.getUnits()
        units.value = response

        // Set default unit if none selected
        if (!selectedUnit.value && response.length > 0 && !isAdmin.value) {
          selectedUnit.value = response[0].id
          authStore.setCurrentUnit(response[0].id)
        }
      } catch (error) {
        console.error('Error loading units:', error)
      }
    }

    const loadStats = async () => {
      if (!isAdmin.value) return

      try {
        const response = await adminAPI.getDashboardStats()
        stats.value = response
      } catch (error) {
        console.error('Error loading stats:', error)
      }
    }

    const loadSuppliers = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
        const response = await fetch(`${API_BASE}/api/v1/suppliers`, {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        })
        if (response.ok) {
          suppliers.value = await response.json()
        }
      } catch (error) {
        console.error('Error loading suppliers:', error)
      }
    }

    const loadRequisitions = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
        const response = await fetch(`${API_BASE}/api/v1/purchase-requisitions`, {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        })
        if (response.ok) {
          requisitions.value = await response.json()
        }
      } catch (error) {
        console.error('Error loading requisitions:', error)
      }
    }

    const getStatusBadgeClass = (status) => {
      const statusClasses = {
        'draft': 'bg-secondary',
        'submitted': 'bg-info',
        'under_review': 'bg-warning',
        'approved': 'bg-success',
        'rejected': 'bg-danger',
        'completed': 'bg-primary'
      }
      return statusClasses[status] || 'bg-secondary'
    }

    const getPriorityBadgeClass = (priority) => {
      const priorityClasses = {
        'low': 'bg-secondary',
        'medium': 'bg-info',
        'high': 'bg-warning',
        'urgent': 'bg-danger'
      }
      return priorityClasses[priority] || 'bg-secondary'
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleDateString()
    }

    const loadDashboardData = async () => {
      loading.value = true
      try {
        await Promise.all([
          loadUnits(),
          loadStats()
        ])
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadDashboardData()
    })

    return {
      activeTab,
      units,
      selectedUnit,
      stats,
      suppliers,
      requisitions,
      loading,
      userName,
      userEmail,
      isAdmin,
      isViewer,
      setActiveTab,
      handleUnitChange,
      handleLogout,
      loadSuppliers,
      loadRequisitions,
      getStatusBadgeClass,
      getPriorityBadgeClass,
      formatDate
    }
  }
}
</script>

<style scoped>
.sidebar {
  min-height: calc(100vh - 56px);
  box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
}

.nav-link {
  color: #333;
  border-radius: 5px;
  margin-bottom: 5px;
}

.nav-link:hover {
  background-color: #e9ecef;
}

.nav-link.active {
  background-color: #0d6efd;
  color: white;
}

.card {
  border: none;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,.1);
}

.navbar-brand {
  font-weight: 600;
}

.dropdown-menu {
  border: none;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stats-card {
  transition: transform 0.2s;
}

.stats-card:hover {
  transform: translateY(-2px);
}
</style>
