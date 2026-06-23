from pydantic import BaseModel, Field
from datetime import date as date_type, datetime
from typing import Optional


# ============ 通用 ============

class PageRequest(BaseModel):
    """分页请求基类"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PageResponse(BaseModel):
    """分页响应"""
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    items: list = Field(default_factory=list, description="数据列表")


class HmsApiResponse(BaseModel):
    """HMS API 通用响应"""
    code: int = Field(default=200)
    msg: str = Field(default="success")
    result: Optional[dict | list] = None


# ============ 科室 ============

class DeptItem(BaseModel):
    """科室信息"""
    id: int
    name: str
    outpatient: Optional[bool] = None
    description: Optional[str] = None
    recommended: Optional[bool] = None


class DeptListRequest(PageRequest):
    """科室列表请求"""
    name: Optional[str] = None


class DeptListResponse(BaseModel):
    """科室列表响应"""
    total: int = 0
    items: list[DeptItem] = Field(default_factory=list)


class DeptDetailRequest(BaseModel):
    """科室详情请求"""
    id: int


class DeptDetailResponse(BaseModel):
    """科室详情响应"""
    id: int
    name: str
    outpatient: Optional[bool] = None
    description: Optional[str] = None
    recommended: Optional[bool] = None
    sub_depts: list["SubDeptItem"] = Field(default_factory=list)


# ============ 诊室 ============

class SubDeptItem(BaseModel):
    """诊室信息"""
    id: int
    name: str
    dept_id: int
    location: str


class SubDeptListRequest(PageRequest):
    """诊室列表请求"""
    dept_id: Optional[int] = None
    name: Optional[str] = None


class SubDeptListResponse(BaseModel):
    """诊室列表响应"""
    total: int = 0
    items: list[SubDeptItem] = Field(default_factory=list)


# ============ 医生 ============

class DoctorItem(BaseModel):
    """医生信息"""
    id: int
    name: str
    sex: Optional[str] = None
    photo: Optional[str] = None
    job: Optional[str] = None
    degree: Optional[str] = None
    school: Optional[str] = None
    description: Optional[str] = None
    tag: Optional[str] = None
    recommended: Optional[bool] = None
    status: Optional[int] = None


class DoctorListRequest(PageRequest):
    """医生列表请求"""
    name: Optional[str] = None
    dept_sub_id: Optional[int] = None


class DoctorListResponse(BaseModel):
    """医生列表响应"""
    total: int = 0
    items: list[DoctorItem] = Field(default_factory=list)


class DoctorDetailResponse(BaseModel):
    """医生详情响应"""
    id: int
    name: str
    sex: Optional[str] = None
    photo: Optional[str] = None
    birthday: Optional[date_type] = None
    school: Optional[str] = None
    degree: Optional[str] = None
    tel: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    job: Optional[str] = None
    remark: Optional[str] = None
    description: Optional[str] = None
    hiredate: Optional[date_type] = None
    tag: Optional[str] = None
    recommended: Optional[bool] = None
    status: Optional[int] = None


# ============ 排班 ============

class ScheduleItem(BaseModel):
    """排班时段"""
    id: int
    work_plan_id: int
    slot: int
    maximum: int
    num: int


class ScheduleListRequest(BaseModel):
    """排班查询请求"""
    dept_sub_id: Optional[int] = None
    date: Optional[str] = None
    doctor_id: Optional[int] = None


class ScheduleListResponse(BaseModel):
    """排班列表响应"""
    items: list[dict] = Field(default_factory=list)


class ScheduleDetailRequest(BaseModel):
    """排班详情请求"""
    work_plan_id: int


class ScheduleDetailResponse(BaseModel):
    """排班详情响应"""
    work_plan_id: int
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    dept_sub_id: Optional[int] = None
    date: Optional[str] = None
    maximum: int = 0
    num: int = 0
    schedules: list[ScheduleItem] = Field(default_factory=list)


# ============ 挂号 ============

class RegistrationCreateRequest(BaseModel):
    """创建挂号请求"""
    patient_card_id: int
    work_plan_id: int
    doctor_schedule_id: int
    doctor_id: int
    dept_sub_id: int
    appointment_date: date_type
    slot: int


class RegistrationCreateResponse(BaseModel):
    """创建挂号响应"""
    id: int
    status: int = 0


class RegistrationQueryRequest(BaseModel):
    """查询挂号请求"""
    patient_card_id: Optional[int] = None
    registration_id: Optional[int] = None


class RegistrationItem(BaseModel):
    """挂号记录"""
    id: int
    patient_card_id: Optional[int] = None
    work_plan_id: Optional[int] = None
    doctor_schedule_id: Optional[int] = None
    doctor_id: Optional[int] = None
    dept_sub_id: Optional[int] = None
    appointment_date: Optional[date_type] = None
    slot: Optional[int] = None
    status: Optional[int] = None
    payment_status: Optional[int] = None
    create_time: Optional[datetime] = None


class RegistrationQueryResponse(BaseModel):
    """查询挂号响应"""
    items: list[RegistrationItem] = Field(default_factory=list)


class RegistrationCancelRequest(BaseModel):
    """取消挂号请求"""
    registration_id: int


class RegistrationCancelResponse(BaseModel):
    """取消挂号响应"""
    result: int = 0


# ============ 患者认证 ============

class SmsCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(pattern=r"^1[3-9]\d{9}$", description="手机号")


class SmsCodeResponse(BaseModel):
    """发送验证码响应"""
    msg: str = "验证码已发送"
    code_dev: Optional[str] = None


class PatientLoginRequest(BaseModel):
    """患者登录请求"""
    phone: str = Field(pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: str = Field(min_length=4, max_length=6, description="验证码")


class PatientLoginResponse(BaseModel):
    """患者登录响应"""
    token: str
    patient_id: int
    name: str


class PatientLogoutResponse(BaseModel):
    """患者登出响应"""
    msg: str = "登出成功"
