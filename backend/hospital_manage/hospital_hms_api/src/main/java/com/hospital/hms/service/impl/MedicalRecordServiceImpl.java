package com.hospital.hms.service.impl;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.MedicalRecordDao;
import com.hospital.hms.pojo.MedicalRecord;
import com.hospital.hms.service.MedicalRecordService;
import cn.hutool.core.map.MapUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class MedicalRecordServiceImpl implements MedicalRecordService {

    @Autowired
    private MedicalRecordDao medicalRecordDao;

    @Override
    public int insertMedicalRecord(MedicalRecord medicalRecord) {
        return medicalRecordDao.insert(medicalRecord);
    }

    @Override
    public int updateMedicalRecord(MedicalRecord medicalRecord) {
        return medicalRecordDao.updateById(medicalRecord);
    }

    @Override
    public MedicalRecord selectById(Integer id) {
        return medicalRecordDao.selectById(id);
    }

    @Override
    public MedicalRecord selectByRegistrationId(Integer registrationId) {
        return medicalRecordDao.selectByRegistrationId(registrationId);
    }

    @Override
    public PageUtils selectByPage(Map<String, Object> map) {
        Long totalCount = medicalRecordDao.selectByPageCount(map);
        int page = MapUtil.getInt(map, "page");
        int length = MapUtil.getInt(map, "length");
        int start = (page - 1) * length;
        map.put("start", start);
        List<HashMap<String, Object>> list = medicalRecordDao.selectByPage(map);
        return new PageUtils(list, totalCount, page, length);
    }

    @Override
    public List<HashMap<String, Object>> selectByPatientId(Integer patientId, Integer deptSubId, Integer doctorId) {
        HashMap<String, Object> param = new HashMap<>();
        param.put("patientId", patientId);
        param.put("deptSubId", deptSubId);
        param.put("doctorId", doctorId);
        return medicalRecordDao.selectByPatientId(param);
    }
}
