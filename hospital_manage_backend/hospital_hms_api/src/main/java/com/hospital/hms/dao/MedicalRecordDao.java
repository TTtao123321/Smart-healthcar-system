package com.hospital.hms.dao;

import com.hospital.hms.pojo.MedicalRecord;
import org.springframework.stereotype.Repository;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public interface MedicalRecordDao {

    int insert(MedicalRecord medicalRecord);

    int updateById(MedicalRecord medicalRecord);

    MedicalRecord selectById(Integer id);

    Long selectByPageCount(Map<String, Object> map);

    List<HashMap<String, Object>> selectByPage(Map<String, Object> map);

    MedicalRecord selectByRegistrationId(Integer registrationId);

    List<HashMap<String, Object>> selectByPatientId(Map<String, Object> map);
}
