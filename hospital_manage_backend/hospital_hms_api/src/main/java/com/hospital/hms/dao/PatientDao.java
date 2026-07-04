package com.hospital.hms.dao;

import com.hospital.hms.pojo.PatientUserInfo;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public interface PatientDao {

    Long selectPatientByPageCount(Map<String, Object> map);

    List<HashMap<String, Object>> selectPatientByPage(Map<String, Object> map);

    HashMap<String, Object> selectPatientInfoById(Integer patientId);

    List<HashMap<String, Object>> selectRegistrationsByPatientId(Map<String, Object> map);

    int insertPatient(PatientUserInfo patient);

    int updatePatientById(PatientUserInfo patient);

    /**
     * 根据手机号查询患者信息
     */
    PatientUserInfo selectPatientByTel(String tel);

    List<HashMap<String, Object>> selectPatientMedicalRecords(@Param("patientId") Integer patientId,
                                                              @Param("startDate") String startDate,
                                                              @Param("endDate") String endDate);

    HashMap<String, Object> selectPatientMedicalRecordDetail(@Param("patientId") Integer patientId,
                                                             @Param("medicalRecordId") Integer medicalRecordId);

    List<HashMap<String, Object>> selectPatientPrescriptions(@Param("patientId") Integer patientId,
                                                             @Param("startDate") String startDate,
                                                             @Param("endDate") String endDate);

    HashMap<String, Object> selectPatientPrescriptionDetail(@Param("patientId") Integer patientId,
                                                            @Param("prescriptionId") Integer prescriptionId);

    List<HashMap<String, Object>> selectPatientPrescriptionItems(@Param("prescriptionId") Integer prescriptionId);

    int updateRegistrationStatus(@Param("id") Integer id, @Param("status") Integer status);
}
