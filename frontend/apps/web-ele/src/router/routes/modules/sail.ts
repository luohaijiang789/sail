import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'mdi:git',
      order: 100,
      title: '仓库管理',
    },
    name: 'Repositories',
    path: '/repositories',
    component: () => import('#/views/repositories/list.vue'),
  },
  {
    meta: {
      icon: 'mdi:radar',
      order: 200,
      title: '扫描',
    },
    name: 'Scans',
    path: '/scans',
    children: [
      {
        name: 'ScanCreate',
        path: 'create',
        component: () => import('#/views/scans/create.vue'),
        meta: {
          title: '创建扫描',
          hideInMenu: true,
          activePath: '/repositories',
        },
      },
      {
        name: 'ScanDetail',
        path: ':id',
        component: () => import('#/views/scans/detail.vue'),
        meta: {
          title: '扫描详情',
          hideInMenu: true,
          activePath: '/repositories',
        },
      },
    ],
  },
  {
    meta: {
      icon: 'mdi:api',
      order: 300,
      title: 'API 资产',
    },
    name: 'ApiAssets',
    path: '/api-assets',
    component: () => import('#/views/api-assets/list.vue'),
  },
  {
    name: 'ApiAssetDetail',
    path: '/api-assets/:id',
    component: () => import('#/views/api-assets/detail.vue'),
    meta: {
      title: 'API 详情',
      hideInMenu: true,
      activePath: '/api-assets',
    },
  },
  {
    meta: {
      icon: 'mdi:bug-outline',
      order: 400,
      title: '漏洞清单',
    },
    name: 'Findings',
    path: '/findings',
    component: () => import('#/views/findings/list.vue'),
  },
  {
    name: 'FindingDetail',
    path: '/findings/:id',
    component: () => import('#/views/findings/detail.vue'),
    meta: {
      title: '漏洞详情',
      hideInMenu: true,
      activePath: '/findings',
    },
  },
];

export default routes;
