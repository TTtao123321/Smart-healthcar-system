package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.pojo.MedicalRecord;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public interface MedicalRecordService {

    int insertMedicalRecord(MedicalRecord medicalRecord);

    int updateMedicalRecord(MedicalRecord medicalRecord);

    MedicalRecord selectById(Integer id);

    MedicalRecord selectByRegistrationId(Integer registrationId);

    PageUtils selectByPage(Map<String, Object> map);

    List<HashMap<String, Object>> selectByPatientId(Integer patientId, Integer deptSubId, Integer doctorId);
}
