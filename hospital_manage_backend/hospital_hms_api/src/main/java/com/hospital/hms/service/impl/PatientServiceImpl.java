package com.hospital.hms.service.impl;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.PatientDao;
import com.hospital.hms.pojo.PatientUserInfo;
import com.hospital.hms.service.MedicalRegistrationService;
import com.hospital.hms.service.PatientService;
import lombok.extern.log4j.Log4j2;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import cn.hutool.core.map.MapUtil;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Log4j2
@Service
public class PatientServiceImpl implements PatientService {

    @Autowired
    private PatientDao patientDao;

    @Autowired
    private MedicalRegistrationService medicalRegistrationService;

    @Override
    public PageUtils selectPatientByPage(Map<String, Object> map) {
        Long totalCount = patientDao.selectPatientByPageCount(map);
        int page = MapUtil.getInt(map, "page");
        int length = MapUtil.getInt(map, "length");
        int start = (page - 1) * length;
        map.put("start", start);
        List<HashMap<String, Object>> list = patientDao.selectPatientByPage(map);
        return new PageUtils(list, totalCount, page, length);
    }

    @Override
    public HashMap<String, Object> selectPatientDetail(Integer patientId, Integer deptSubId, Integer doctorId) {
        HashMap<String, Object> patientInfo = patientDao.selectPatientInfoById(patientId);
        HashMap<String, Object> param = new HashMap<>();
        param.put("patientId", patientId);
        param.put("deptSubId", deptSubId);
        param.put("doctorId", doctorId);
        List<HashMap<String, Object>> registrations = patientDao.selectRegistrationsByPatientId(param);
        HashMap<String, Object> result = new HashMap<>();
        result.put("patientInfo", patientInfo);
        result.put("registrations", registrations);
        return result;
    }

    @Override
    public int insertPatient(PatientUserInfo patient) {
        return patientDao.insertPatient(patient);
    }

    @Override
    public int updatePatient(PatientUserInfo patient) {
        return patientDao.updatePatientById(patient);
    }

    @Override
    public int updateRegistrationStatus(Integer id, Integer status) {
        if (status != null && status == -1) {
            return medicalRegistrationService.cancelRegistration(id);
        }
        return patientDao.updateRegistrationStatus(id, status);
    }

}
