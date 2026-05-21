package com.hospital.hms.service.impl;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.PatientDao;
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
    public HashMap<String, Object> selectPatientDetail(Integer patientCardId) {
        HashMap<String, Object> patientInfo = patientDao.selectPatientInfoById(patientCardId);
        List<HashMap<String, Object>> registrations = patientDao.selectRegistrationsByPatientId(patientCardId);
        HashMap<String, Object> result = new HashMap<>();
        result.put("patientInfo", patientInfo);
        result.put("registrations", registrations);
        return result;
    }
}
