<template>
  <div v-if="isAuth(['ROOT', 'PATIENT:SELECT'])">
    <el-form :inline="true" :model="dataForm" ref="dataForm">
      <el-form-item prop="name">
        <el-input
          v-model="dataForm.name"
          placeholder="患者姓名"
          size="medium"
          class="input"
          clearable="clearable"
        />
      </el-form-item>
      <el-form-item>
        <el-select v-model="dataForm.sex" class="input" placeholder="性别" size="medium" clearable="clearable">
          <el-option label="男" value="男"/>
          <el-option label="女" value="女"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="dataForm.deptId"
          class="input"
          placeholder="科室"
          size="medium"
          clearable="clearable"
          @change="loadDeptSubList"
        >
          <el-option v-for="one in deptList" :label="one.name" :value="one.id" :key="one.id"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="dataForm.deptSubId"
          class="input"
          placeholder="诊室"
          size="medium"
          clearable="clearable"
        >
          <el-option v-for="one in deptSubList" :label="one.name" :value="one.id" :key="one.id"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="dataForm.doctorId"
          class="input"
          placeholder="就诊医师"
          size="medium"
          clearable="clearable"
        >
          <el-option v-for="one in doctorList" :label="one.name" :value="one.id" :key="one.id"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="dataForm.status"
          class="input"
          placeholder="就诊状态"
          size="medium"
          clearable="clearable"
        >
          <el-option label="待就诊" :value="0"/>
          <el-option label="就诊中" :value="1"/>
          <el-option label="已就诊" :value="2"/>
          <el-option label="复诊中" :value="3"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button size="medium" type="primary" @click="searchHandle()">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table
      :data="dataList"
      border
      v-loading="dataListLoading"
      :cell-style="{ padding: '3px 0' }"
      size="medium"
      style="width: 100%;"
    >
      <el-table-column type="index" header-align="center" align="center" width="60" label="序号">
        <template #default="scope">
          <span>{{ (pageIndex - 1) * pageSize + scope.$index + 1 }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" header-align="center" align="center" label="姓名" min-width="100"/>
      <el-table-column prop="sex" header-align="center" align="center" label="性别" min-width="60"/>
      <el-table-column prop="deptName" header-align="center" align="center" label="科室" min-width="130"/>
      <el-table-column prop="deptSubName" header-align="center" align="center" label="诊室" min-width="150"/>
      <el-table-column prop="doctorName" header-align="center" align="center" label="就诊医师" min-width="100"/>
      <el-table-column prop="date" header-align="center" align="center" label="就诊日期" min-width="120"/>
      <el-table-column header-align="center" align="center" label="时段" min-width="120">
        <template #default="scope">
          <span>{{ slotMap[scope.row.slot] || scope.row.slot }}</span>
        </template>
      </el-table-column>
      <el-table-column header-align="center" align="center" label="状态" min-width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 0" type="info">待就诊</el-tag>
          <el-tag v-else-if="scope.row.status === 1" type="warning">就诊中</el-tag>
          <el-tag v-else-if="scope.row.status === 2" type="success">已就诊</el-tag>
          <el-tag v-else-if="scope.row.status === 3" type="danger">复诊中</el-tag>
        </template>
      </el-table-column>
      <el-table-column header-align="center" align="center" width="100" label="操作">
        <template #default="scope">
          <el-button type="text" size="medium" @click="detailHandle(scope.row.patientCardId)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      @size-change="sizeChangeHandle"
      @current-change="currentChangeHandle"
      :current-page="pageIndex"
      :page-sizes="[10, 20, 50]"
      :page-size="pageSize"
      :total="totalCount"
      layout="total, sizes, prev, pager, next, jumper"
    ></el-pagination>

    <el-dialog v-model="detailVisible" title="患者详情" width="800px" :close-on-click-modal="false">
      <div v-if="patientInfo">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="姓名">{{ patientInfo.name }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ patientInfo.sex }}</el-descriptions-item>
          <el-descriptions-item label="身份证号">{{ patientInfo.pid }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ patientInfo.tel }}</el-descriptions-item>
          <el-descriptions-item label="出生日期">{{ patientInfo.birthday }}</el-descriptions-item>
          <el-descriptions-item label="疾病史">{{ patientInfo.medicalHistory }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <el-divider content-position="left">就诊记录</el-divider>
      <el-table :data="registrations" border size="small" style="width: 100%;" empty-text="暂无就诊记录">
        <el-table-column prop="date" header-align="center" align="center" label="日期" min-width="120"/>
        <el-table-column header-align="center" align="center" label="时段" min-width="120">
          <template #default="scope">
            <span>{{ slotMap[scope.row.slot] || scope.row.slot }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="deptName" header-align="center" align="center" label="科室" min-width="120"/>
        <el-table-column prop="deptSubName" header-align="center" align="center" label="诊室" min-width="130"/>
        <el-table-column prop="doctorName" header-align="center" align="center" label="医师" min-width="100"/>
        <el-table-column header-align="center" align="center" label="状态" min-width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.status === 0" type="info">待就诊</el-tag>
            <el-tag v-else-if="scope.row.status === 1" type="warning">就诊中</el-tag>
            <el-tag v-else-if="scope.row.status === 2" type="success">已就诊</el-tag>
            <el-tag v-else-if="scope.row.status === 3" type="danger">复诊中</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="diagnosis" header-align="center" align="center" label="诊断结果" min-width="200">
          <template #default="scope">
            <span v-if="scope.row.diagnosis">{{ scope.row.diagnosis }}</span>
            <span v-else style="color: #999;">暂无</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
export default {
  data() {
    return {
      dataForm: {
        name: '',
        sex: '',
        deptId: '',
        deptSubId: '',
        doctorId: '',
        status: ''
      },
      dataList: [],
      deptList: [],
      deptSubList: [],
      doctorList: [],
      pageIndex: 1,
      pageSize: 10,
      totalCount: 0,
      dataListLoading: false,
      detailVisible: false,
      patientInfo: null,
      registrations: [],
      slotMap: {
        1: '08:00-08:30', 2: '08:30-09:00', 3: '09:00-09:30',
        4: '09:30-10:00', 5: '10:00-10:30', 6: '10:30-11:00',
        7: '11:00-11:30', 8: '11:30-12:00', 9: '13:00-13:30',
        10: '13:30-14:00', 11: '14:00-14:30', 12: '14:30-15:00',
        13: '15:00-15:30', 14: '15:30-16:00', 15: '16:00-16:30'
      }
    };
  },
  methods: {
    loadDataList() {
      let that = this;
      that.dataListLoading = true;
      let data = {
        name: that.dataForm.name || null,
        sex: that.dataForm.sex || null,
        deptId: that.dataForm.deptId || null,
        deptSubId: that.dataForm.deptSubId || null,
        doctorId: that.dataForm.doctorId || null,
        status: that.dataForm.status !== '' ? that.dataForm.status : null,
        page: that.pageIndex,
        length: that.pageSize
      };
      that.$http('patient/selectByPage', 'POST', data, true, function(resp) {
        let page = resp.result;
        that.dataList = page.list;
        that.totalCount = page.totalCount;
        that.dataListLoading = false;
      });
    },
    loadDeptList() {
      let that = this;
      that.$http('medical/dept/selectAllDeptNameAndId', 'GET', null, true, function(resp) {
        that.deptList = resp.list;
      });
    },
    loadDeptSubList() {
      let that = this;
      that.deptSubList = [];
      that.dataForm.deptSubId = '';
      if (that.dataForm.deptId) {
        that.$http('medical/dept/sub/selectByDeptId?deptId=' + that.dataForm.deptId, 'GET', null, true, function(resp) {
          that.deptSubList = resp.list || [];
        });
      }
    },
    loadDoctorList() {
      let that = this;
      that.$http('doctor/selectAllDoctorNameAndId', 'GET', null, true, function(resp) {
        that.doctorList = resp.list || [];
      });
    },
    searchHandle() {
      if (this.pageIndex != 1) {
        this.pageIndex = 1;
      }
      this.loadDataList();
    },
    sizeChangeHandle(val) {
      this.pageSize = val;
      this.pageIndex = 1;
      this.loadDataList();
    },
    currentChangeHandle(val) {
      this.pageIndex = val;
      this.loadDataList();
    },
    detailHandle(patientCardId) {
      let that = this;
      that.detailVisible = true;
      that.$http('patient/selectDetail', 'POST', { patientCardId: patientCardId }, true, function(resp) {
        that.patientInfo = resp.patientInfo;
        if (that.patientInfo.medicalHistory) {
          try {
            let arr = JSON.parse(that.patientInfo.medicalHistory);
            that.patientInfo.medicalHistory = arr.join('、');
          } catch (e) {}
        }
        that.registrations = resp.registrations || [];
      });
    }
  },
  created() {
    this.loadDataList();
    this.loadDeptList();
    this.loadDoctorList();
  }
};
</script>
