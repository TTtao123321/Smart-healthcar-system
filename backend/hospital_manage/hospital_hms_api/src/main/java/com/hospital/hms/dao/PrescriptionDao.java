package com.hospital.hms.dao;

import com.hospital.hms.pojo.Prescription;
import org.springframework.stereotype.Repository;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public interface PrescriptionDao {

    int insert(Prescription prescription);

    int updateStatus(Prescription prescription);

    Prescription selectById(Integer id);

    List<HashMap<String, Object>> selectByMedicalRecordId(Integer medicalRecordId);

    List<HashMap<String, Object>> selectByPatientId(Map<String, Object> map);

    Long selectByPatientIdCount(Map<String, Object> map);

    int deleteItemsByPrescriptionId(Integer prescriptionId);

    int deleteById(Integer id);
}
