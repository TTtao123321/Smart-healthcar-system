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

    int updateRegistrationStatus(@Param("id") Integer id, @Param("status") Integer status);
}
