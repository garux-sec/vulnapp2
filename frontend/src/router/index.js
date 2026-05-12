import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import Dashboard from '../components/Dashboard.vue'
import ContractList from '../components/ContractList.vue'
import ContractDetail from '../components/ContractDetail.vue'
import AdminPanel from '../components/AdminPanel.vue'
import Profile from '../components/Profile.vue'

const routes = [
  { path: '/',          component: Login },
  { path: '/dashboard', component: Dashboard },
  { path: '/contracts', component: ContractList },
  { path: '/contracts/:id', component: ContractDetail },
  { path: '/admin',     component: AdminPanel },
  { path: '/profile',   component: Profile },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// VULNERABLE: Route guard only checks localStorage — forged token passes
router.beforeEach((to, from, next) => {
  const publicRoutes = ['/']
  if (!publicRoutes.includes(to.path)) {
    // VULNERABLE #17: Auth check reads from localStorage — easily tampered
    const token = localStorage.getItem('token')
    if (!token) return next('/')
  }
  next()
})

export default router
