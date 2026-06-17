<template>
  <div v-if="isAuth(['ROOT', 'MEDICAL:SELECT'])">
    <!-- 搜索条件 -->
    <el-form :inline="true" :model="dataForm" ref="dataForm">
      <el-form-item prop="name">
        <el-input v-model="dataForm.name" placeholder="患者姓名" size="medium" class="input" clearable />
      </el-form-item>
      <el-form-item>
        <el-select v-model="dataForm.sex" class="input" placeholder="性别" size="medium" clearable>
          <el-option label="男" value="男" />
          <el-option label="女" value="女" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="dataForm.deptId" class="input" placeholder="科室" size="medium" clearable @change="loadDeptSubList">
          <el-option v-for="one in deptList" :label="one.name" :value="one.id" :key="one.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="dataForm.deptSubId" class="input" placeholder="诊室" size="medium" clearable>
          <el-option v-for="one in deptSubList" :label="one.name" :value="one.id" :key="one.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="dataForm.doctorId" class="input" placeholder="就诊医师" size="medium" clearable>
          <el-option v-for="one in doctorList" :label="one.name" :value="one.id" :key="one.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="dataForm.status" class="input" placeholder="就诊状态" size="medium" clearable>
          <el-option label="待就诊" :value="0" />
          <el-option label="就诊中" :value="1" />
          <el-option label="已就诊" :value="2" />
          <el-option label="复诊中" :value="3" />
          <el-option label="完成就诊" :value="4" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button size="medium" type="primary" @click="searchHandle()">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
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
      <el-table-column prop="name" header-align="center" align="center" label="姓名" min-width="100" />
      <el-table-column prop="sex" header-align="center" align="center" label="性别" min-width="60" />
      <el-table-column prop="deptName" header-align="center" align="center" label="科室" min-width="130" />
      <el-table-column prop="deptSubName" header-align="center" align="center" label="诊室" min-width="150" />
      <el-table-column prop="doctorName" header-align="center" align="center" label="就诊医师" min-width="100" />
      <el-table-column prop="date" header-align="center" align="center" label="就诊日期" min-width="120" />
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
          <el-tag v-else-if="scope.row.status === 4" type="">完成就诊</el-tag>
        </template>
      </el-table-column>
      <el-table-column header-align="center" align="center" width="220" label="操作">
        <template #default="scope">
          <div class="action-buttons">
            <el-button type="primary" link size="small" @click="detailHandle(scope.row)">
              <el-icon><View /></el-icon>详情
            </el-button>
            <template v-if="isAuth(['ROOT', 'MEDICAL:UPDATE']) && scope.row.status === 0">
              <el-divider direction="vertical" />
              <el-button type="success" link size="small" @click="acceptPatientHandle(scope.row)">
                <el-icon><Check /></el-icon>已接诊
              </el-button>
            </template>
            <template v-else-if="isAuth(['ROOT', 'MEDICAL:UPDATE']) && scope.row.status === 1">
              <el-divider direction="vertical" />
              <el-button type="warning" link size="small" @click="writeRecordHandle(scope.row)">
                <el-icon><EditPen /></el-icon>写病历
              </el-button>
            </template>
            <template v-else-if="(scope.row.status === 2 || scope.row.status === 3 || scope.row.status === 4) && scope.row.medicalRecordId">
              <el-divider direction="vertical" />
              <el-button type="success" link size="small" @click="viewRecordHandle(scope.row)">
                <el-icon><Document /></el-icon>看病历
              </el-button>
            </template>
            <template v-else>
              <el-divider direction="vertical" />
              <span class="action-placeholder"></span>
            </template>
          </div>
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
    />

    <!-- 患者详情弹窗 -->
    <el-dialog v-model="detailVisible" title="" width="960px" :close-on-click-modal="false" custom-class="patient-detail-dialog">
      <div v-if="patientInfo" class="patient-detail">
        <!-- 患者基本信息卡片 -->
        <div class="patient-profile-card">
          <div class="profile-header">
            <div class="profile-avatar">
              <span class="avatar-text">{{ patientInfo.name ? patientInfo.name.charAt(0) : '' }}</span>
            </div>
            <div class="profile-title">
              <h2 class="patient-name">{{ patientInfo.name }}</h2>
              <div class="patient-tags">
                <el-tag :type="patientInfo.sex === '男' ? '' : 'danger'" size="small" effect="dark">{{ patientInfo.sex }}</el-tag>
                <el-tag type="info" size="small" effect="plain">{{ insuranceTypeMap[patientInfo.insuranceType] || '未填写' }}</el-tag>
              </div>
            </div>
          </div>
          <div class="profile-grid">
            <div class="profile-item">
              <span class="item-label">身份证号</span>
              <span class="item-value">{{ patientInfo.pid || '—' }}</span>
            </div>
            <div class="profile-item">
              <span class="item-label">手机号</span>
              <span class="item-value">{{ patientInfo.tel || '—' }}</span>
            </div>
            <div class="profile-item">
              <span class="item-label">出生日期</span>
              <span class="item-value">{{ patientInfo.birthday || '—' }}</span>
            </div>
          </div>
        </div>
        <!-- 病史信息卡片 -->
        <div class="patient-history-card">
          <div class="history-section">
            <div class="history-item">
              <span class="history-label">既往史</span>
              <span class="history-value">{{ patientInfo.medicalHistory || '无' }}</span>
            </div>
            <div class="history-item">
              <span class="history-label">过敏史</span>
              <span class="history-value" :class="{ 'has-allergy': patientInfo.allergyHistory }">{{ patientInfo.allergyHistory || '无' }}</span>
            </div>
            <div class="history-item">
              <span class="history-label">家族史</span>
              <span class="history-value">{{ patientInfo.familyHistory || '无' }}</span>
            </div>
          </div>
        </div>
        <!-- 就诊记录区域 -->
        <div class="patient-records-section">
          <div class="section-header">
            <div class="section-indicator"></div>
            <h3 class="section-title">就诊病历</h3>
            <span class="section-count">共 {{ registrations.length }} 条记录</span>
          </div>
          <el-table :data="registrations" border size="small" style="width: 100%;" empty-text="暂无就诊记录" class="records-table">
            <el-table-column prop="date" header-align="center" align="center" label="日期" min-width="120" />
            <el-table-column header-align="center" align="center" label="时段" min-width="120">
              <template #default="scope">
                <span>{{ slotMap[scope.row.slot] || scope.row.slot }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="deptName" header-align="center" align="center" label="科室" min-width="120" />
            <el-table-column prop="doctorName" header-align="center" align="center" label="医师" min-width="100" />
            <el-table-column header-align="center" align="center" label="状态" min-width="100">
              <template #default="scope">
                <el-tag v-if="scope.row.status === 0" type="info" size="small">待就诊</el-tag>
                <el-tag v-else-if="scope.row.status === 1" type="warning" size="small">就诊中</el-tag>
                <el-tag v-else-if="scope.row.status === 2" type="success" size="small">已就诊</el-tag>
                <el-tag v-else-if="scope.row.status === 3" type="danger" size="small">复诊中</el-tag>
                <el-tag v-else-if="scope.row.status === 4" size="small">完成就诊</el-tag>
              </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" label="诊断结果" min-width="200">
              <template #default="scope">
                <span v-if="scope.row.diagnosis" class="diagnosis-text">{{ scope.row.diagnosis }}</span>
                <span v-else class="empty-text">暂无</span>
              </template>
            </el-table-column>

          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button v-if="isAuth(['ROOT', 'MEDICAL:UPDATE']) && hasActiveRegistration" type="primary" @click="editPatientHandle">编辑患者</el-button>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑患者弹窗 -->
    <el-dialog v-model="patientFormVisible" title="编辑患者" width="600px" :close-on-click-modal="false">
      <el-form :model="patientForm" :rules="patientRules" ref="patientFormRef" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="patientForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="性别" prop="sex">
          <el-select v-model="patientForm.sex" placeholder="请选择性别">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="身份证号" prop="pid">
          <el-input v-model="patientForm.pid" placeholder="请输入身份证号" />
        </el-form-item>
        <el-form-item label="手机号" prop="tel">
          <el-input v-model="patientForm.tel" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="出生日期" prop="birthday">
          <el-date-picker v-model="patientForm.birthday" type="date" value-format="YYYY-MM-DD" placeholder="请选择出生日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="医保类型" prop="insuranceType">
          <el-select v-model="patientForm.insuranceType" placeholder="请选择医保类型" style="width: 100%;">
            <el-option label="自费" :value="0" />
            <el-option label="城镇职工" :value="1" />
            <el-option label="城乡居民" :value="2" />
            <el-option label="新农合" :value="3" />
            <el-option label="商业保险" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="既往史">
          <el-input v-model="patientForm.medicalHistory" type="textarea" :rows="2" placeholder="请输入既往史" />
        </el-form-item>
        <el-form-item label="过敏史">
          <el-input v-model="patientForm.allergyHistory" type="textarea" :rows="2" placeholder="请输入过敏史" />
        </el-form-item>
        <el-form-item label="家族史">
          <el-input v-model="patientForm.familyHistory" type="textarea" :rows="2" placeholder="请输入家族史" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="patientFormVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPatientForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 写病历弹窗 -->
    <el-dialog v-model="recordFormVisible" title="填写门诊病历" width="700px" :close-on-click-modal="false">
      <el-form :model="recordForm" ref="recordFormRef" label-width="100px">
        <el-form-item label="主诉" prop="chiefComplaint">
          <el-input v-model="recordForm.chiefComplaint" type="textarea" :rows="2" placeholder="请输入主诉" />
        </el-form-item>
        <el-form-item label="现病史">
          <el-input v-model="recordForm.presentIllness" type="textarea" :rows="3" placeholder="请输入现病史" />
        </el-form-item>
        <el-form-item label="体格检查">
          <el-input v-model="recordForm.physicalExam" type="textarea" :rows="2" placeholder="请输入体格检查结果" />
        </el-form-item>
        <el-form-item label="诊断结果" prop="diagnosis">
          <el-input v-model="recordForm.diagnosis" placeholder="请输入诊断结果" />
        </el-form-item>
        <el-form-item label="医嘱">
          <el-input v-model="recordForm.doctorAdvice" type="textarea" :rows="2" placeholder="请输入医嘱" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="recordForm.remark" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordFormVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRecordForm">保存病历</el-button>
      </template>
    </el-dialog>

    <!-- 查看病历弹窗 -->
    <el-dialog v-model="recordViewVisible" title="门诊病历详情" width="800px" :close-on-click-modal="false">
      <!-- 多病历切换按钮 -->
      <div v-if="recordList.length > 1" class="record-switch-bar">
        <el-radio-group v-model="currentRecordIndex" size="small">
          <el-radio-button v-for="(rec, idx) in recordList" :key="rec.id" :label="idx">
            {{ rec.date }} {{ slotMap[rec.slot] || '' }}
          </el-radio-button>
        </el-radio-group>
      </div>
      <div v-if="currentRecord">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="主诉" :span="2">{{ currentRecord.chiefComplaint || '无' }}</el-descriptions-item>
          <el-descriptions-item label="现病史" :span="2">{{ currentRecord.presentIllness || '无' }}</el-descriptions-item>
          <el-descriptions-item label="体格检查" :span="2">{{ currentRecord.physicalExam || '无' }}</el-descriptions-item>
          <el-descriptions-item label="诊断结果">{{ currentRecord.diagnosis || '无' }}</el-descriptions-item>
          <el-descriptions-item label="医嘱">{{ currentRecord.doctorAdvice || '无' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ currentRecord.remark || '无' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <el-divider content-position="left">处方记录</el-divider>
      <div v-if="prescriptionList.length > 0">
        <div v-for="(rx, index) in prescriptionList" :key="rx.id" style="margin-bottom: 15px;">
          <el-card shadow="never">
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>处方 {{ index + 1 }}（{{ rx.type === 0 ? '西药' : '中药' }}）</span>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-tag v-if="rx.status === 0" type="info">待取药</el-tag>
                  <el-tag v-else-if="rx.status === 1" type="success">已取药</el-tag>
                  <el-tag v-else-if="rx.status === 2" type="danger">已退药</el-tag>
                  <el-button v-if="!isCompletedVisit" type="danger" link size="small" @click="deletePrescriptionHandle(rx.id)">
                    <el-icon><Delete /></el-icon>删除
                  </el-button>
                </div>
              </div>
            </template>
            <el-table :data="rx.items" border size="small" empty-text="暂无药品明细">
              <el-table-column prop="drugName" header-align="center" align="center" label="药品名称" min-width="120" />
              <el-table-column prop="specification" header-align="center" align="center" label="规格" min-width="80" />
              <el-table-column prop="quantity" header-align="center" align="center" label="数量" width="70" />
              <el-table-column prop="dosage" header-align="center" align="center" label="用法用量" min-width="120" />
              <el-table-column prop="frequency" header-align="center" align="center" label="频次" min-width="80" />
              <el-table-column prop="days" header-align="center" align="center" label="天数" width="70" />
              <el-table-column prop="remark" header-align="center" align="center" label="备注" min-width="100" />
            </el-table>
          </el-card>
        </div>
      </div>
      <div v-else style="color: #999; text-align: center; padding: 10px;">暂无处方</div>
      <template #footer>
        <el-button v-if="isAuth(['ROOT', 'MEDICAL:INSERT']) && currentRecord && !isCompletedVisit" type="primary" @click="addPrescriptionHandle">开处方</el-button>
        <el-button v-if="currentRecord && currentRowStatus === 2" type="danger" @click="finishVisitHandle">结束就诊</el-button>
        <el-button @click="recordViewVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 开处方弹窗 -->
    <el-dialog v-model="prescriptionFormVisible" title="开具处方" width="800px" :close-on-click-modal="false">
      <el-form :model="prescriptionForm" ref="prescriptionFormRef" label-width="100px">
        <el-form-item label="处方类型">
          <el-select v-model="prescriptionForm.type" placeholder="请选择处方类型">
            <el-option label="西药" :value="0" />
            <el-option label="中药" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="药品明细">
          <el-table :data="prescriptionForm.items" border size="small" style="width: 100%;">
            <el-table-column header-align="center" align="center" label="药品名称" min-width="120">
              <template #default="scope">
                <el-input v-model="scope.row.drugName" size="small" placeholder="药品名称" />
              </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" label="规格" min-width="80">
              <template #default="scope">
                <el-input v-model="scope.row.specification" size="small" placeholder="规格" />
              </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" label="数量" width="80">
              <template #default="scope">
                <el-input-number v-model="scope.row.quantity" size="small" :min="1" controls-position="right" />
              </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" label="用法用量" min-width="120">
              <template #default="scope">
                <el-input v-model="scope.row.dosage" size="small" placeholder="用法用量" />
              </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" label="频次" min-width="80">
              <template #default="scope">
                <el-input v-model="scope.row.frequency" size="small" placeholder="频次" />
              </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" label="天数" width="80">
              <template #default="scope">
                <el-input-number v-model="scope.row.days" size="small" :min="1" controls-position="right" />
              </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" label="操作" width="70">
              <template #default="scope">
                <el-button type="text" size="small" style="color: #f56c6c;" @click="removeDrugItem(scope.$index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-button type="primary" size="small" @click="addDrugItem" style="margin-top: 10px;">添加药品</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="prescriptionFormVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPrescriptionForm">确定</el-button>
      </template>
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
      // 详情弹窗
      detailVisible: false,
      patientInfo: null,
      registrations: [],
      // 新增/编辑患者弹窗
      patientFormVisible: false,
      patientForm: {
        id: null,
        name: '',
        sex: '',
        pid: '',
        tel: '',
        birthday: '',
        medicalHistory: '',
        allergyHistory: '',
        familyHistory: '',
        insuranceType: null
      },
      patientRules: {
        name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
        sex: [{ required: true, message: '请选择性别', trigger: 'change' }],
        pid: [{ required: true, message: '请输入身份证号', trigger: 'blur' }],
        tel: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
        birthday: [{ required: true, message: '请选择出生日期', trigger: 'change' }]
      },
      // 写病历弹窗
      recordFormVisible: false,
      recordForm: {
        registrationId: null,
        patientId: null,
        doctorId: null,
        deptSubId: null,
        chiefComplaint: '',
        presentIllness: '',
        physicalExam: '',
        diagnosis: '',
        doctorAdvice: '',
        remark: ''
      },
      // 查看病历弹窗
      recordViewVisible: false,
      recordList: [],
      currentRecordIndex: 0,
      currentRecord: null,
      currentRowStatus: null,
      currentRegistrationId: null,
      prescriptionList: [],
      // 开处方弹窗
      prescriptionFormVisible: false,
      prescriptionForm: {
        medicalRecordId: null,
        patientId: null,
        doctorId: null,
        type: 0,
        items: []
      },
      // 映射
      slotMap: {
        1: '08:00-08:30', 2: '08:30-09:00', 3: '09:00-09:30',
        4: '09:30-10:00', 5: '10:00-10:30', 6: '10:30-11:00',
        7: '11:00-11:30', 8: '11:30-12:00', 9: '13:00-13:30',
        10: '13:30-14:00', 11: '14:00-14:30', 12: '14:30-15:00',
        13: '15:00-15:30', 14: '15:30-16:00', 15: '16:00-16:30'
      },
      insuranceTypeMap: {
        0: '自费', 1: '城镇职工', 2: '城乡居民', 3: '新农合', 4: '商业保险'
      }
    };
  },
  computed: {
    hasActiveRegistration() {
      if (!this.registrations || this.registrations.length === 0) return false;
      return this.registrations.some(r => r.status !== 4);
    },
    isCompletedVisit() {
      return this.currentRowStatus === 4;
    }
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
        that.deptList = resp.result;
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
    // 已接诊
    acceptPatientHandle(row) {
      let that = this;
      that.$confirm('确认已接诊该患者？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        that.$http('patient/updateRegistrationStatus', 'POST', { id: row.registrationId, status: 1 }, true, function(resp) {
          that.$message.success('已接诊');
          that.loadDataList();
        });
      }).catch(() => {});
    },
    // 患者详情
    detailHandle(row) {
      let that = this;
      that.detailVisible = true;
      that.$http('patient/selectDetail', 'POST', {
        patientCardId: row.patientCardId,
        deptSubId: row.deptSubId || null,
        doctorId: row.doctorId || null
      }, true, function(resp) {
        that.patientInfo = resp.patientInfo;
        if (that.patientInfo.medicalHistory) {
          try {
            let arr = JSON.parse(that.patientInfo.medicalHistory);
            that.patientInfo.medicalHistory = arr.join('、');
          } catch (e) {}
        }
        that.registrations = resp.registrations || [];
      });
    },
    // 编辑患者
    editPatientHandle() {
      if (!this.patientInfo) return;
      this.patientForm = {
        id: this.patientInfo.patientCardId,
        name: this.patientInfo.name || '',
        sex: this.patientInfo.sex || '',
        pid: this.patientInfo.pid || '',
        tel: this.patientInfo.tel || '',
        birthday: this.patientInfo.birthday || '',
        medicalHistory: this.patientInfo.medicalHistory || '',
        allergyHistory: this.patientInfo.allergyHistory || '',
        familyHistory: this.patientInfo.familyHistory || '',
        insuranceType: this.patientInfo.insuranceType
      };
      this.patientFormVisible = true;
      this.$nextTick(() => { this.$refs.patientFormRef && this.$refs.patientFormRef.clearValidate(); });
    },
    // 提交患者表单
    submitPatientForm() {
      let that = this;
      that.$refs.patientFormRef.validate(valid => {
        if (!valid) return;
        that.$http('patient/update', 'POST', that.patientForm, true, function(resp) {
          that.$message.success('修改成功');
          that.patientFormVisible = false;
          that.detailVisible = false;
          that.loadDataList();
        });
      });
    },
    // 写病历
    writeRecordHandle(row) {
      this.recordForm = {
        registrationId: row.registrationId,
        patientId: row.patientCardId,
        doctorId: row.doctorId || null,
        deptSubId: row.deptSubId || null,
        chiefComplaint: '',
        presentIllness: '',
        physicalExam: '',
        diagnosis: '',
        doctorAdvice: '',
        remark: ''
      };
      this.recordFormVisible = true;
    },
    // 提交病历
    submitRecordForm() {
      let that = this;
      if (!that.recordForm.chiefComplaint) {
        that.$message.warning('请输入主诉');
        return;
      }
      that.$http('medical_record/insert', 'POST', that.recordForm, true, function(resp) {
        that.$message.success('病历保存成功');
        that.recordFormVisible = false;
        // 自动更新挂号状态为已就诊
        that.$http('patient/updateRegistrationStatus', 'POST', { id: that.recordForm.registrationId, status: 2 }, true, function(resp2) {
          that.loadDataList();
        });
      });
    },
    // 查看病历
    viewRecordHandle(row) {
      let that = this;
      that.recordViewVisible = true;
      that.recordList = [];
      that.currentRecordIndex = 0;
      that.currentRecord = null;
      that.prescriptionList = [];
      that.currentRowStatus = null;
      that.currentRegistrationId = null;
      that.$http('medical_record/selectByPatientId', 'POST', {
        patientId: row.patientCardId,
        deptSubId: row.deptSubId || null,
        doctorId: row.doctorId || null
      }, true, function(resp) {
        that.recordList = resp.result || [];
        if (that.recordList.length > 0) {
          let rec = that.recordList[0];
          that.currentRowStatus = rec.status;
          that.currentRegistrationId = rec.registrationId;
          that.loadRecordDetail(rec.id);
        }
      });
    },
    // 加载病历详情和处方
    loadRecordDetail(medicalRecordId) {
      let that = this;
      that.currentRecord = null;
      that.prescriptionList = [];
      that.$http('medical_record/selectById', 'POST', { id: medicalRecordId }, true, function(resp) {
        that.currentRecord = resp.result;
        that.$http('prescription/selectByMedicalRecordId', 'POST', { medicalRecordId: medicalRecordId }, true, function(resp2) {
          let prescriptions = resp2.result || [];
          that.prescriptionList = prescriptions;
          prescriptions.forEach(function(rx, idx) {
            that.$http('prescription/selectItemsByPrescriptionId', 'POST', { prescriptionId: rx.id }, true, function(resp3) {
              that.prescriptionList[idx].items = resp3.result || [];
            });
          });
        });
      });
    },
    // 开处方
    addPrescriptionHandle() {
      if (!this.currentRecord) return;
      this.prescriptionForm = {
        medicalRecordId: this.currentRecord.id,
        patientId: this.currentRecord.patientId,
        doctorId: this.currentRecord.doctorId,
        type: 0,
        items: [{ drugName: '', specification: '', quantity: 1, dosage: '', frequency: '', days: 3, remark: '' }]
      };
      this.prescriptionFormVisible = true;
    },
    addDrugItem() {
      this.prescriptionForm.items.push({ drugName: '', specification: '', quantity: 1, dosage: '', frequency: '', days: 3, remark: '' });
    },
    removeDrugItem(index) {
      this.prescriptionForm.items.splice(index, 1);
    },
    submitPrescriptionForm() {
      let that = this;
      if (that.prescriptionForm.items.length === 0) {
        that.$message.warning('请添加药品明细');
        return;
      }
      let hasEmpty = that.prescriptionForm.items.some(item => !item.drugName);
      if (hasEmpty) {
        that.$message.warning('请填写药品名称');
        return;
      }
      that.$http('prescription/insert', 'POST', that.prescriptionForm, true, function(resp) {
        that.$message.success('处方开具成功');
        that.prescriptionFormVisible = false;
        // 刷新处方列表
        if (that.currentRecord) {
          that.loadRecordDetail(that.currentRecord.id);
        }
      });
    },
    // 删除处方
    deletePrescriptionHandle(prescriptionId) {
      let that = this;
      that.$confirm('确认删除该处方？删除后不可恢复。', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        that.$http('prescription/deleteById', 'POST', { id: prescriptionId }, true, function(resp) {
          that.$message.success('处方已删除');
          if (that.currentRecord) {
            that.loadRecordDetail(that.currentRecord.id);
          }
        });
      }).catch(() => {});
    },
    // 结束就诊
    finishVisitHandle() {
      let that = this;
      that.$confirm('确认结束就诊？结束后患者信息将不可修改。', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        that.$http('patient/updateRegistrationStatus', 'POST', { id: that.currentRegistrationId, status: 4 }, true, function(resp) {
          that.$message.success('已结束就诊');
          that.recordViewVisible = false;
          that.currentRowStatus = 4;
          that.loadDataList();
        });
      }).catch(() => {});
    }
  },
  created() {
    this.loadDataList();
    this.loadDeptList();
    this.loadDoctorList();
  },
  watch: {
    currentRecordIndex(val) {
      if (this.recordList.length > 0 && this.recordList[val]) {
        this.loadRecordDetail(this.recordList[val].id);
      }
    }
  }
};
</script>

<style lang="less" scoped>
/* 患者详情弹窗样式 */
.patient-detail {
  .patient-profile-card {
    background: linear-gradient(135deg, #f0f5ff 0%, #e8f0fe 100%);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    border: 1px solid #d4e4fc;

    .profile-header {
      display: flex;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid rgba(64, 158, 255, 0.15);
    }

    .profile-avatar {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: linear-gradient(135deg, #409EFF, #66b1ff);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16px;
      flex-shrink: 0;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);

      .avatar-text {
        font-size: 24px;
        font-weight: 600;
        color: #fff;
        letter-spacing: 1px;
      }
    }

    .profile-title {
      .patient-name {
        font-size: 22px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 6px 0;
        letter-spacing: 1px;
        line-height: 1.3;
      }

      .patient-tags {
        display: flex;
        gap: 8px;
      }
    }

    .profile-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }

    .profile-item {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .item-label {
        font-size: 12px;
        color: #8c8c8c;
        font-weight: 400;
        letter-spacing: 0.5px;
        text-transform: uppercase;
      }

      .item-value {
        font-size: 15px;
        color: #1a1a2e;
        font-weight: 500;
        letter-spacing: 0.3px;
      }
    }
  }

  .patient-history-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    border: 1px solid #e8e8e8;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);

    .history-section {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }

    .history-item {
      background: #fafafa;
      border-radius: 8px;
      padding: 14px 16px;
      border: 1px solid #f0f0f0;
      transition: all 0.2s ease;

      &:hover {
        background: #f5f5f5;
        border-color: #e0e0e0;
      }

      .history-label {
        display: block;
        font-size: 12px;
        color: #8c8c8c;
        font-weight: 500;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
      }

      .history-value {
        display: block;
        font-size: 14px;
        color: #303133;
        font-weight: 400;
        line-height: 1.6;
        word-break: break-all;

        &.has-allergy {
          color: #e6a23c;
          font-weight: 500;
        }
      }
    }
  }

  .patient-records-section {
    .section-header {
      display: flex;
      align-items: center;
      margin-bottom: 14px;
      gap: 10px;

      .section-indicator {
        width: 4px;
        height: 20px;
        background: linear-gradient(180deg, #409EFF, #66b1ff);
        border-radius: 2px;
      }

      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #1a1a2e;
        margin: 0;
        letter-spacing: 0.5px;
      }

      .section-count {
        font-size: 12px;
        color: #8c8c8c;
        margin-left: auto;
        background: #f5f7fa;
        padding: 2px 10px;
        border-radius: 10px;
      }
    }

    .records-table {
      border-radius: 8px;
      overflow: hidden;

      .diagnosis-text {
        color: #303133;
        font-weight: 500;
      }

      .empty-text {
        color: #bfbfbf;
        font-style: italic;
      }
    }
  }

  .record-switch-bar {
    margin-bottom: 16px;
    padding: 12px 16px;
    background: #f5f7fa;
    border-radius: 8px;
    border: 1px solid #e4e7ed;

    .el-radio-group {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
  }
}
</style>

<style lang="less">
/* 患者详情弹窗全局样式（不使用 scoped） */
.patient-detail-dialog {
  .el-dialog__header {
    padding: 0;
    height: 0;
  }

  .el-dialog__body {
    padding: 24px 28px;
    max-height: 70vh;
    overflow-y: auto;
  }

  .el-dialog__footer {
    border-top: 1px solid #f0f0f0;
    padding: 14px 28px;
  }
}

.action-buttons {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.action-placeholder {
  display: inline-block;
  width: 52px;
}
</style>
ENDOFFILE; __tr_native_ec=$?; pwd -P >| '/var/folders/hn/1ylcxx294sz85pbtym3z3h880000gn/T/agent-toolhost/jobs/job-912c31bca5f54e519c0001b338f3c090/cwd.txt'; exit "$__tr_native_ec"