package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.pojo.PatientUserInfo;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public interface PatientService {

    PageUtils selectPatientByPage(Map<String, Object> map);

    HashMap<String, Object> selectPatientDetail(Integer patientId, Integer deptSubId, Integer doctorId);

    int insertPatient(PatientUserInfo patient);

    int updatePatient(PatientUserInfo patient);

    int updateRegistrationStatus(Integer id, Integer status);
}
