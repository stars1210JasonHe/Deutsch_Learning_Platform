import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import SearchHistory from '@/views/SearchHistory.vue'
import ExamResults from '@/views/ExamResults.vue'

// Phase 2 Views (lazy loaded)
const ExamList = () => import('@/views/ExamList.vue')
const ExamTake = () => import('@/views/ExamTake.vue')
const SRSReview = () => import('@/views/SRSReview.vue')
const Dashboard = () => import('@/views/Dashboard.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: Register,
      meta: { requiresGuest: true }
    },
    {
      path: '/history',
      name: 'SearchHistory',
      component: SearchHistory,
      meta: { requiresAuth: true }
    },
    
    // Phase 2 Routes - Exam System
    {
      path: '/exams',
      name: 'ExamList',
      component: ExamList,
      meta: { requiresAuth: true }
    },
    {
      path: '/exam/:id',
      name: 'ExamTake',
      component: ExamTake,
      meta: { requiresAuth: true }
    },
    {
      path: '/exam/:id/results/:attemptId',
      name: 'ExamResults',
      component: ExamResults,
      meta: { requiresAuth: true }
    },
    
    // Phase 2 Routes - SRS System
    {
      path: '/srs',
      name: 'SRSReview',
      component: SRSReview,
      meta: { requiresAuth: true }
    },
    
    // Phase 2 Routes - Analytics
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    }
  ]
})

// Route guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router