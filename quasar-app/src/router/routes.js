// const routes = [
//   {
//     path: '/',
//     component: () => import('layouts/MainLayout.vue'),
//     children: [
//       { path: '', component: () => import('pages/IndexPage.vue') },
//       { path: 'login', component: () => import('pages/LoginPage.vue') },
//       { path: 'expire', component: () => import('pages/ExpiredPage.vue') }
//     ]
//   },

//   {
//     path: '/:catchAll(.*)*',
//     component: () => import('pages/ErrorNotFound.vue')
//   }
// ]


// export default routes
const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: 'home',
        component: () => import('pages/IndexPage.vue'),
        meta: { requiresAuth: true }  // 🔒 Protected
      },
      {
        path: '',
        component: () => import('pages/LoginPage.vue')
      },
      {
        path: 'expire',
        component: () => import('pages/ExpiredPage.vue')
      }
    ]
  },

  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
