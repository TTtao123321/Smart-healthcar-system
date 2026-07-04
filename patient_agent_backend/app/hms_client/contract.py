from dataclasses import dataclass
from typing import Type

from app.hms_client.models import (
    DeptListRequest, DeptListResponse,
    DeptDetailRequest, DeptDetailResponse,
    SubDeptListRequest, SubDeptListResponse,
    DoctorListRequest, DoctorListResponse,
    DoctorDetailResponse,
    ScheduleListRequest, ScheduleListResponse,
    ScheduleDetailRequest, ScheduleDetailResponse,
    RegistrationCreateRequest, RegistrationCreateResponse,
    RegistrationQueryRequest, RegistrationQueryResponse,
    RegistrationCancelRequest, RegistrationCancelResponse,
    MedicalRecordListResponse, MedicalRecordDetailResponse,
    PrescriptionListResponse, PrescriptionDetailResponse,
    SmsCodeRequest, SmsCodeResponse,
    PatientLoginRequest, PatientLoginResponse,
    PatientLogoutResponse,
)


@dataclass
class RequestResponsePair:
    request: Type
    response: Type


# 科室服务契约
DeptServiceContract = {
    "list": RequestResponsePair(request=DeptListRequest, response=DeptListResponse),
    "detail": RequestResponsePair(request=DeptDetailRequest, response=DeptDetailResponse),
}

# 诊室服务契约
SubDeptServiceContract = {
    "list": RequestResponsePair(request=SubDeptListRequest, response=SubDeptListResponse),
}

# 医生服务契约
DoctorServiceContract = {
    "list": RequestResponsePair(request=DoctorListRequest, response=DoctorListResponse),
    "detail": RequestResponsePair(request=DeptDetailRequest, response=DoctorDetailResponse),
}

# 排班服务契约
ScheduleServiceContract = {
    "list": RequestResponsePair(request=ScheduleListRequest, response=ScheduleListResponse),
    "detail": RequestResponsePair(request=ScheduleDetailRequest, response=ScheduleDetailResponse),
}

# 挂号服务契约
RegistrationServiceContract = {
    "create": RequestResponsePair(request=RegistrationCreateRequest, response=RegistrationCreateResponse),
    "query": RequestResponsePair(request=RegistrationQueryRequest, response=RegistrationQueryResponse),
    "cancel": RequestResponsePair(request=RegistrationCancelRequest, response=RegistrationCancelResponse),
}

# 患者结果查询契约
MedicalRecordServiceContract = {
    "list": RequestResponsePair(request=None, response=MedicalRecordListResponse),
    "detail": RequestResponsePair(request=None, response=MedicalRecordDetailResponse),
}

PrescriptionServiceContract = {
    "list": RequestResponsePair(request=None, response=PrescriptionListResponse),
    "detail": RequestResponsePair(request=None, response=PrescriptionDetailResponse),
}

# 患者认证契约
AuthServiceContract = {
    "send_sms": RequestResponsePair(request=SmsCodeRequest, response=SmsCodeResponse),
    "login": RequestResponsePair(request=PatientLoginRequest, response=PatientLoginResponse),
    "logout": RequestResponsePair(request=None, response=PatientLogoutResponse),
}
