import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import ContractList from '../components/ContractList.vue'
import ContractDetail from '../components/ContractDetail.vue'
import AdminPanel from '../components/AdminPanel.vue'
import Profile from '../components/Profile.vue'

const routes = [
  { path: '/',             redirect: '/dashboard' },
  { path: '/dashboard',    component: Dashboard },
  { path: '/contracts',    component: ContractList },
  { path: '/contracts/:id', component: ContractDetail },
  { path: '/admin',        component: AdminPanel },
  { path: '/profile',      component: Profile },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
