export const scheduleDateLabel = '2026年6月24日 周三'

export const scheduleDepartments = [
  {
    departmentId: 'dept-internal',
    departmentName: '内科',
    doctors: [
      {
        doctorId: 'doctor-001',
        doctorName: '张明华',
        title: '主任医师',
        bio: '擅长心血管疾病诊疗，30年临床经验',
        departmentName: '内科',
        timeSlots: ['08:00-12:00', '14:00-17:00'],
      },
      {
        doctorId: 'doctor-002',
        doctorName: '李芳',
        title: '副主任医师',
        bio: '呼吸系统疾病专家，擅长慢性病管理',
        departmentName: '内科',
        timeSlots: ['08:30-11:30'],
      },
    ],
  },
  {
    departmentId: 'dept-surgery',
    departmentName: '外科',
    doctors: [
      {
        doctorId: 'doctor-003',
        doctorName: '王建国',
        title: '主任医师',
        bio: '普外科及微创手术专家',
        departmentName: '外科',
        timeSlots: ['09:00-12:00', '14:00-18:00'],
      },
      {
        doctorId: 'doctor-004',
        doctorName: '赵雪梅',
        title: '主治医师',
        bio: '骨科与运动损伤康复',
        departmentName: '外科',
        timeSlots: ['14:00-17:00'],
      },
    ],
  },
  {
    departmentId: 'dept-pediatrics',
    departmentName: '儿科',
    doctors: [
      {
        doctorId: 'doctor-005',
        doctorName: '陈小慧',
        title: '副主任医师',
        bio: '儿童呼吸及消化系统疾病',
        departmentName: '儿科',
        timeSlots: ['08:30-12:00', '14:00-16:30'],
      },
    ],
  },
  {
    departmentId: 'dept-ob',
    departmentName: '妇产科',
    doctors: [
      {
        doctorId: 'doctor-006',
        doctorName: '刘美玲',
        title: '主任医师',
        bio: '高危妊娠管理及妇科微创手术',
        departmentName: '妇产科',
        timeSlots: ['08:00-12:00', '14:00-17:30'],
      },
    ],
  },
]
