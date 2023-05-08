<template>
  <div>
    <div style=position:absolute;left:10px;top:700px;>
      <div style=float:left;padding-left:100px;padding-right:20px :style="{width: '440px', height: '360px'}">
        <LineChart v-if="flag" id='commit-chart' :SID="sid" :Meaning="meaning" :Xdata="months" :Series="commit_series" :style="{width: '400px', height: '300px'}"></LineChart>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import LineChart from './LineChart'
export default {
  name: 'HelloWorld',
  data () {
    return {
      msg: 'Welcome to Your Vue.js App',
      months: [],
      commit_series: [],
      meaning: [],
      sid: '',
      flag: false
    }
  },
  methods: {
    getData () {
      var that = this
      const path = 'http://127.0.0.1:5000/sample'
      axios.get(path).then(function (response) {
        // 这里服务器返回的 response 为一个 json object，可通过如下方法需要转成 json 字符串
        // 可以直接通过 response.data 取key-value
        // 坑一：这里不能直接使用 this 指针，不然找不到对象
        var msg = response.data
        that.sid = 'commit-chart'
        that.months = msg.months
        that.meaning = new Array(0)
        that.meaning.push('Total Commit')
        that.meaning.push('fix')
        that.meaning.push('other')
        that.meaning.push('feature')
        that.commit_series = new Array(0)
        that.commit_series.push({
          name: 'Total Commit',
          type: 'line',
          data: msg.commit_count
        })
        that.commit_series.push({
          name: 'fix',
          type: 'line',
          data: msg.fix_count
        })
        that.commit_series.push({
          name: 'other',
          type: 'line',
          data: msg.other_count
        })
        that.commit_series.push({
          name: 'feature',
          type: 'line',
          data: msg.feature_count
        })
        that.flag = true
      }).catch(function (error) {
        alert('Error ' + error)
      })
    }
  },
  components: {
    LineChart
  },
  created: function () {
    // alert('openstack created')
    let that = this
    that.flag = false
    that.$nextTick(function () {
      // alert('before get data')
      that.getData()
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
