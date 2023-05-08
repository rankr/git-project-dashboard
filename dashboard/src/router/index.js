import Vue from 'vue'
import Router from 'vue-router'
// import HelloWorld from '@/components/HelloWorld'
import ListRepo from '@/components/ListRepo'
import CommitState from '@/components/CommitState'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      // name: 'HelloWorld',
      // component: HelloWorld
      name: 'ListRepo',
      component: ListRepo
    },
    {
      path: '/commit_state',
      name: 'CommitState',
      component: CommitState
    }
  ]
})
