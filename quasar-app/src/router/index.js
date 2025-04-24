// import { defineRouter } from '#q-app/wrappers'
// import {
//   createRouter,
//   createMemoryHistory,
//   createWebHistory,
//   createWebHashHistory
// } from 'vue-router'
// import routes from './routes'
// import { useAuthStore } from 'stores/auth'

// export default defineRouter(function ({ store /* , ssrContext */ }) {
//   const createHistory = process.env.SERVER
//     ? createMemoryHistory
//     : (process.env.VUE_ROUTER_MODE === 'history'
//         ? createWebHistory
//         : createWebHashHistory)

//   const Router = createRouter({
//     scrollBehavior: () => ({ left: 0, top: 0 }),
//     routes,
//     history: createHistory(process.env.VUE_ROUTER_BASE)
//   })

//   // ───────────────────────────────────────────
//   // Global auth guard
//   // ───────────────────────────────────────────
//   Router.beforeEach(to => {
//     // get Pinia auth store
//     const auth = useAuthStore(store)

//     // redirect guests trying to open protected pages
//     if (to.meta.requiresAuth && !auth.token) {
//       return { path: '/login', query: { redirect: to.fullPath } }
//     }

//     // prevent logged‑in users from opening guest‑only pages (login/register)
//     if (to.meta.guestOnly && auth.token) {
//       return { path: '/' }
//     }
//   })

//   return Router
// })
import { route } from 'quasar/wrappers'
import { createRouter, createMemoryHistory, createWebHistory, createWebHashHistory } from 'vue-router'
import routes from './routes'
import { useAuthStore } from 'stores/auth'

export default route(function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : (process.env.VUE_ROUTER_MODE === 'history' ? createWebHistory : createWebHashHistory)

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createHistory(process.env.VUE_ROUTER_BASE)
  })

  // 🔐 Route Guard for Auth
  Router.beforeEach((to, from, next) => {
    const auth = useAuthStore()
    const isProtected = to.matched.some(record => record.meta.requiresAuth)

    if (isProtected && !auth.token) {
      next('/login')
    } else {
      next()
    }
  })

  return Router
})

