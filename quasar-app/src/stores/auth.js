// src/stores/auth.js
import { defineStore } from 'pinia'
import { api } from 'boot/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || ''
  }),
  getters: {
    isAuthenticated: (state) => !!state.token
  },
  actions: {
    // Initialize auth headers on app startup
    init() {
      if (this.token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      }
    },
    async login(email, password) {
      try {
        const response = await api.post('/login', { email, password })
        this.token = response.data.token
        this.user = response.data.user
        localStorage.setItem('token', this.token)
        api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        return true
      } catch (err) {
        throw err.response.data.message || 'Login failed'
      }
    },
    async register(email, username, password, repassword) {
      try {
        const response = await api.post('/register', { email, username, password, repassword })
        return response.data
      } catch (err) {
        throw err.response.data.message || 'Registration failed'
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      delete api.defaults.headers.common['Authorization']
    }
  }
})
