<template>
  <div>
    <div style=position:absolute;left:10px;top:150px;>
      <div style=float:left;padding-left:100px;padding-right:20px :style="{width: '440px', height: '360px'}">
        <button v-on:click="get_repo_list()">列出所有仓库</button>
        <button v-on:click="hide_repo_list()">隐藏所有仓库</button>
        <br/>
        <ul style="list-style: outside;list-style-type: none;">
          <li v-for="item in items" v-bind:key="item" v-if="flag">
            <router-link :to="{name:'CommitState', query: {repo_name: item.name}}"> {{ item.name }} </router-link>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'HelloWorld',
  data () {
    return {
      msg: 'Welcome to Your Vue.js App',
      items: [],
      flag: false
    }
  },
  methods: {
    get_repo_list () {
      var that = this
      const path = 'http://127.0.0.1:5000/repo_list'
      axios.get(path).then(function (response) {
        // 这里服务器返回的 response 为一个 json object，可通过如下方法需要转成 json 字符串
        // 可以直接通过 response.data 取key-value
        // 坑一：这里不能直接使用 this 指针，不然找不到对象
        var msg = response.data
        that.items = new Array(0)
        for (var name in msg) {
          that.items.push({
            'name': name,
            'path': msg[name]
          })
        }
        that.flag = true
      }).catch(function (error) {
        alert('Error ' + error)
      })
    },
    hide_repo_list () {
      var that = this
      that.flag = false
    }
  },
  created: function () {
    // alert('openstack created')
    let that = this
    that.flag = false
    that.$nextTick(function () {
      // alert('before get data')
      // that.getData()
      // alert('after get data')
    })
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.center-block {
  margin: 0 auto;
}
.cc {
  margin: 0 auto;
  width: 600px;
}
.intro {
  text-align: left;
  padding-left: 60px;
  font-size: large;
}
</style>
