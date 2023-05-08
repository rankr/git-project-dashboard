<template>
  <div>

  </div>
</template>

<script>
import axios from 'axios'
import PieGraph from './PieGraph'
import LineChart from './LineChart'
import qs from 'qs'

export default {
  name: 'Company',
  data () {
    return {
    }
  },
  methods: {
    getData () {
      var that = this
      
    },
    change (msg) {
      let that = this
      that.select_company = msg
      that.getData()
    }
  },
  components: {
    PieGraph,
    LineChart
  },
  created: function () {
    // alert('company created')
    // alert(this.filtered_list.length)
    let that = this
    that.flag = false
    that.$nextTick(function () {
      // alert('company before get data')
      that.getData()
      // alert('company after get data')
    })
  }
}
</script>

<style scoped>
.center-block {
  margin: 0 auto;
}
.text-block {
  padding-left: 300px;
  margin: 0 auto;
}
.intro {
  font-weight: bold;
  width: 600px;
  float: left;
  text-align: left;
  font-size: 20px;
  font-family: Tahoma;
  height: 40px;
}
.attr {
  font-family: "Hiragino Sans GB";
  font-weight: normal;
}
</style>
