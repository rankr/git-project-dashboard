<template>
  <div>
    <div style=position:absolute;left:10px;top:150px;>
      <div>
        <table>
          <tr>
            <th>
              <label class="typo__label">Start Month</label>
              <multiselect v-model="start" :options="select_months" :searchable="false" :close-on-select="false" :show-labels="false" placeholder="Pick a value"></multiselect>
            </th>
            <th>
              <label class="typo__label">End Month</label>
              <multiselect v-model="end" :options="select_months" :searchable="false" :close-on-select="false" :show-labels="false" placeholder="Pick a value"></multiselect>
            </th>
          </tr>
        </table>
      </div>
      <br/>
      <br/>
      <br/>
      <div style=float:left;padding-left:200px;padding-right:20px :style="{width: '440px', height: '360px'}">
        <h2> Commit History of Project {{ repo_name }} </h2>
        <LineChart v-if="flag" id='commit-state-chart' :SID="sid" :Meaning="meaning" :Xdata="months" :Series="commit_series" :style="{width: '400px', height: '300px'}"></LineChart>
      </div>
      <br/>
      <br/>
      <br/>
      <div style=float:left;padding-left:200px;>
        <h2> File Change History of Project {{ repo_name }} </h2>
        <p>
          <body style="font-size:20px;text-align:left;">Important Modified Files from {{ start }} to {{ end }}:</body>
          <ul style="list-style-type:none;text-align:left;">
            <li v-for="(value, key) in summary_file_data" v-bind:key="key">
              &nbsp;&nbsp; <b>{{ key }}</b> <br/>
              &nbsp;&nbsp;&nbsp;&nbsp; <b>Modified lines:</b> {{ value['total'] }} <br/>
              &nbsp;&nbsp;&nbsp;&nbsp; <b>Commits:</b> {{ value['commit'] }} <br/>
              &nbsp;&nbsp;&nbsp;&nbsp; <b>Core Developers:</b> {{ value['core_developer'] }} <br/>
              <br/>
            </li>
          </ul>
        </p>
        <table>
          <tr>
            <th width='300px'>
              C: Commit Amount<br/>
              L: Modified Line Amount<br/>
              CD: Core Developers
            </th>
            <th v-for="month in months" v-bind:key="month" width='200px'> {{month}} </th>
          </tr>
          <tr v-for="file in display_file" v-bind:key="file">
            <td width='300px'>{{file}}</td>
            <td v-for="file_data in display_file_data[file]" v-bind:key="file_data" width='200px'>
              C: {{file_data['commit']}}<br/>
              L: {{file_data['total']}}<br/>
              CD: {{file_data['core_developer']}}
            </td>
          </tr>
        </table>
      </div>
      <br/>
      <br/>
      <br/>
      <div style=float:left;padding-left:200px;>
        <h2> Developer Contribution History of Project {{ repo_name }} </h2>
        <p>
          <body style="font-size:20px;text-align:left;">Important Developers from {{ start }} to {{ end }}:</body>
          <ul style="list-style-type:none;text-align:left;">
            <li v-for="(value, key) in summary_developer_data" v-bind:key="key">
              &nbsp;&nbsp; <b>{{ key }}</b> <br/>
              &nbsp;&nbsp;&nbsp;&nbsp; <b>Do Feature:</b> {{ value['feature'] }} <br/>
              &nbsp;&nbsp;&nbsp;&nbsp; <b>Do Fix:</b> {{ value['fix'] }} <br/>
              &nbsp;&nbsp;&nbsp;&nbsp; <b>Do Other:</b> {{ value['other'] }} <br/>
              &nbsp;&nbsp;&nbsp;&nbsp; <b>Total:</b> {{ value['commit'] }} <br/>
              <br/>
            </li>
          </ul>
        </p>
        <table>
          <tr>
            <th width='300px'>
              Feat: Feature Amount<br/>
              Fix: Fix Amount<br/>
              Other: Other Amount<br/>
              Total: Commit Amount<br/>
            </th>
            <th v-for="month in months" v-bind:key="month" width='200px'> {{month}} </th>
          </tr>
          <tr v-for="developer in display_developer" v-bind:key="developer">
            <td width='300px'>{{developer}}</td>
            <td v-for="developer_data in display_developer_data[developer]" v-bind:key="developer_data" width='200px'>
              Feat: {{developer_data['feature']}}<br/>
              Fix: {{developer_data['fix']}}<br/>
              Other: {{developer_data['other']}}<br/>
              Total: {{developer_data['commit']}}
            </td>
          </tr>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Multiselect from 'vue-multiselect'
import LineChart from './LineChart'
export default {
  name: 'HelloWorld',
  data () {
    return {
      msg: 'Welcome to Your Vue.js App',
      items: [],
      repo_name: '',
      commit_state_data: [],
      file_state_data: [],
      developer_state_data: [],
      select_months: [
        '2020_1', '2020_2', '2020_3', '2020_4', '2020_5', '2020_6', '2020_7', '2020_8', '2020_9', '2020_10', '2020_11', '2020_12',
        '2021_1', '2021_2', '2021_3', '2021_4', '2021_5', '2021_6', '2021_7', '2021_8', '2021_9', '2021_10', '2021_11', '2021_12',
        '2022_1', '2022_2', '2022_3', '2022_4', '2022_5', '2022_6', '2022_7', '2022_8', '2022_9', '2022_10', '2022_11', '2022_12',
        '2023_1', '2023_2', '2023_3', '2023_4'
      ],
      months: [],
      commit_series: [],
      meaning: [],
      sid: '',
      flag: false,
      start: '2020_1',
      end: '2023_4',
      display_file: [],
      display_file_data: [],
      summary_file_data: [],
      display_developer: [],
      display_developer_data: [],
      summary_developer_data: []
    }
  },
  watch: {
    start (val, oldVal) {
      var that = this
      if (that.date_compare(that.start, that.end) === 1) {
        that.end = that.start
      }
      that.draw_commit_state(that.commit_state_data)
      that.prepare_file_state(that.file_state_data)
      that.prepare_developer_state(that.developer_state_data)
    },
    end (val, oldVal) {
      var that = this
      if (that.date_compare(that.start, that.end) === 1) {
        that.end = that.start
      }
      that.draw_commit_state(that.commit_state_data)
      that.prepare_file_state(that.file_state_data)
      that.prepare_developer_state(that.developer_state_data)
    }
  },
  methods: {
    get_commit_state () {
      var that = this
      that.repo_name = that.$route.query.repo_name
      if (that.date_compare(that.start, that.end) === 1) {
        that.end = that.start
      }
      const path = 'http://127.0.0.1:5000/commit_state/' + that.repo_name
      axios.get(path).then(function (response) {
        // 这里服务器返回的 response 为一个 json object，可通过如下方法需要转成 json 字符串
        // 可以直接通过 response.data 取key-value
        // 坑一：这里不能直接使用 this 指针，不然找不到对象
        var msg = response.data
        that.commit_state_data = msg
        that.draw_commit_state(that.commit_state_data)
        that.flag = true
      }).catch(function (error) {
        alert('Error ' + error)
      })
    },
    get_file_state () {
      var that = this
      that.repo_name = that.$route.query.repo_name
      if (!that.date_compare(that.start, that.end)) {
        that.end = that.start
      }
      const path = 'http://127.0.0.1:5000/file_state/' + that.repo_name
      axios.get(path).then(function (response) {
        // 这里服务器返回的 response 为一个 json object，可通过如下方法需要转成 json 字符串
        // 可以直接通过 response.data 取key-value
        // 坑一：这里不能直接使用 this 指针，不然找不到对象
        var msg = response.data
        that.file_state_data = msg
        that.display_file = msg.default_path
        that.prepare_file_state(msg)
      }).catch(function (error) {
        alert('Error ' + error)
      })
    },
    get_developer_state () {
      var that = this
      that.repo_name = that.$route.query.repo_name
      if (!that.date_compare(that.start, that.end)) {
        that.end = that.start
      }
      const path = 'http://127.0.0.1:5000/developer_state/' + that.repo_name
      axios.get(path).then(function (response) {
        // 这里服务器返回的 response 为一个 json object，可通过如下方法需要转成 json 字符串
        // 可以直接通过 response.data 取key-value
        // 坑一：这里不能直接使用 this 指针，不然找不到对象
        var msg = response.data
        that.developer_state_data = msg
        that.display_developer = msg.default_developer
        that.prepare_developer_state(msg)
      }).catch(function (error) {
        alert('Error ' + error)
      })
    },
    draw_commit_state (obj) {
      var that = this
      that.meaning = new Array(0)
      that.meaning.push('Total Commit')
      that.meaning.push('fix')
      that.meaning.push('other')
      that.meaning.push('feature')

      var fixArr = new Array(0)
      var featureArr = new Array(0)
      var otherArr = new Array(0)
      that.months = new Array(0)
      that.commit_series = new Array(0)

      that.sid = 'commit-state-chart'
      for (var month in obj) {
        if (that.date_compare(that.start, month) !== 1 && that.date_compare(month, that.end) !== 1) {
          that.months.push(month)
        }
      }
      that.months.sort(that.date_compare)
      for (var i in that.months) {
        month = that.months[i]
        if (!obj.hasOwnProperty(month)) {
          fixArr.push(0)
          featureArr.push(0)
          otherArr.push(0)
          continue
        }
        fixArr.push(obj[month]['fix'])
        featureArr.push(obj[month]['feature'])
        otherArr.push(obj[month]['other'])
      }
      that.commit_series.push({
        name: 'fix',
        type: 'line',
        data: fixArr
      })
      that.commit_series.push({
        name: 'other',
        type: 'line',
        data: featureArr
      })
      that.commit_series.push({
        name: 'feature',
        type: 'line',
        data: otherArr
      })
    },
    prepare_file_state (obj) {
      var that = this
      // lert(that.display_file)
      that.display_file_data = {}
      that.summary_file_data = {}
      for (var path in obj) {
        if (path === 'default_path') { // 用来传递默认展示路径的，不需要下面的处理
          continue
        }
        if (that.display_file.indexOf(path) === -1) { // 不在展示路径里，直接pass
          continue
        }
        var pathInfo = obj[path]
        // console.log("=================pathInfo")
        // console.log(pathInfo.hasOwnProperty('2020_2'))
        // console.log(pathInfo)
        for (var i in that.months) {
          var month = that.months[i]
          if (!that.display_file_data.hasOwnProperty(path)) {
            that.display_file_data[path] = new Array(0)
            that.summary_file_data[path] = {'total': 0, 'commit': 0, 'core_developer': ''}
          }
          if (!pathInfo.hasOwnProperty(month)) { // 当前路径没有这个month信息
            that.display_file_data[path].push({
              'total': 0,
              'commit': 0,
              'core_developer': ''
            })
            continue
          }
          var monthInfo = pathInfo[month]
          if (that.date_compare(that.start, month) !== 1 && that.date_compare(month, that.end) !== 1) {
            that.display_file_data[path].push({
              'total': monthInfo['total'],
              'commit': monthInfo['commit'],
              'core_developer': monthInfo['core_developer']
            })
            that.summary_file_data[path]['total'] += monthInfo['total']
            that.summary_file_data[path]['commit'] += monthInfo['commit']
            if (that.summary_file_data[path]['core_developer'] === '') {
              that.summary_file_data[path]['core_developer'] += monthInfo['core_developer']
            } else {
              that.summary_file_data[path]['core_developer'] += ', ' + monthInfo['core_developer']
            }
          }
        }
        // console.log(that.display_file_data['src/click/core.py'])
      }
    },
    prepare_developer_state (obj) {
      var that = this
      // alert(that.display_file)
      console.log('=================display_developer')
      console.log(that.display_developer)
      that.display_developer_data = {}
      that.summary_developer_data = {}
      for (var developer in obj) {
        if (developer === 'default_developer') { // 用来传递默认展示路径的，不需要下面的处理
          continue
        }
        if (that.display_developer.indexOf(developer) === -1) { // 不在展示路径里，直接pass
          continue
        }
        var developerInfo = obj[developer]
        // console.log("=================developerInfo")
        // console.log(developerInfo.hasOwnProperty('2020_2'))
        // console.log(developerInfo)
        for (var i in that.months) {
          var month = that.months[i]
          if (!that.display_developer_data.hasOwnProperty(developer)) {
            that.display_developer_data[developer] = new Array(0)
            that.summary_developer_data[developer] = {'feature': 0, 'fix': 0, 'other': 0, 'commit': 0}
          }
          if (!developerInfo.hasOwnProperty(month)) { // 当前路径没有这个month信息
            that.display_developer_data[developer].push({
              'feature': 0,
              'fix': 0,
              'other': 0,
              'commit': 0
            })
            continue
          }
          var monthInfo = developerInfo[month]
          if (that.date_compare(that.start, month) !== 1 && that.date_compare(month, that.end) !== 1) {
            that.display_developer_data[developer].push({
              'feature': monthInfo['feature'],
              'fix': monthInfo['fix'],
              'other': monthInfo['other'],
              'commit': monthInfo['commit']
            })
            that.summary_developer_data[developer]['feature'] += monthInfo['feature']
            that.summary_developer_data[developer]['fix'] += monthInfo['fix']
            that.summary_developer_data[developer]['other'] += monthInfo['other']
            that.summary_developer_data[developer]['commit'] += monthInfo['commit']
          }
        }
        // console.log(that.display_developer_data['KP'])
      }
    },
    hide_repo_list () {
      var that = this
      that.flag = false
    },
    date_compare (a, b) {
      var arr = a.split('_')
      var starttime = new Date(arr[0], arr[1])
      var starttimes = starttime.getTime()
      var arrs = b.split('_')
      var lktime = new Date(arrs[0], arrs[1])
      var lktimes = lktime.getTime()
      if (starttimes > lktimes) {
        return 1
      } else if (starttimes < lktimes) {
        return -1
      } else {
        return 0
      }
    }
  },
  components: {
    LineChart,
    Multiselect
  },
  created: function () {
    // alert('openstack created')
    let that = this
    that.flag = false
    that.$nextTick(function () {
      // alert('before get data')
      that.get_commit_state()
      that.get_file_state()
      that.get_developer_state()
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
tr {
  border-bottom: 1px solid #ddd;
}
th {
  border-bottom: 2px solid #ddd;
}
tr:nth-child(even) {
  background-color: rgba(150, 212, 212, 0.4);
}
th:nth-child(even),td:nth-child(even) {
  background-color: rgba(150, 212, 212, 0.4);
}
</style>
