package com.hospital.hms.dao;

import org.springframework.stereotype.Repository;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public interface PatientDao {

    Long selectPatientByPageCount(Map<String, Object> map);

    List<HashMap<String, Object>> selectPatientByPage(Map<String, Object> map);

    HashMap<String, Object> selectPatientInfoById(Integer patientCardId);

    List<HashMap<String, Object>> selectRegistrationsByPatientId(Integer patientCardId);
}
