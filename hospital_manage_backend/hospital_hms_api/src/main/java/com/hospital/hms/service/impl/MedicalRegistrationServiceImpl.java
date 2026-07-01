package com.hospital.hms.service.impl;

import cn.hutool.core.map.MapUtil;
import com.hospital.common.exception.GlobalException;
import com.hospital.hms.dao.MedicalRegistrationDao;
import com.hospital.hms.dao.PatientDao;
import com.hospital.hms.pojo.MedicalRegistration;
import com.hospital.hms.service.MedicalRegistrationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;

@Service
public class MedicalRegistrationServiceImpl implements MedicalRegistrationService {

    @Autowired
    private MedicalRegistrationDao medicalRegistrationDao;

    @Autowired
    private PatientDao patientDao;

    @Override
    @Transactional
    public int save(MedicalRegistration entity) {
        HashMap<String, Object> patient = patientDao.selectPatientInfoById(entity.getPatientId());
        if (patient == null) {
            throw new GlobalException("患者不存在");
        }

        HashMap<String, Object> schedule = medicalRegistrationDao.selectScheduleForUpdate(entity.getDoctorScheduleId());
        if (schedule == null) {
            throw new GlobalException("排班不存在");
        }

        String workPlanStatus = MapUtil.getStr(schedule, "workPlanStatus", "ACTIVE");
        if (!"ACTIVE".equals(workPlanStatus)) {
            throw new GlobalException("当前排班已停诊");
        }

        int maximum = MapUtil.getInt(schedule, "maximum", 0);
        int num = MapUtil.getInt(schedule, "num", 0);
        if (num >= maximum) {
            throw new GlobalException("当前号源已满");
        }

        entity.setStatus(0);
        entity.setPaymentStatus(0);
        medicalRegistrationDao.insert(entity);
        medicalRegistrationDao.increaseScheduleNum(entity.getDoctorScheduleId());
        return entity.getId();
    }

    @Override
    @Transactional
    public int cancelRegistration(Integer registrationId) {
        HashMap<String, Object> registration = medicalRegistrationDao.selectRegistrationById(registrationId);
        if (registration == null) {
            throw new GlobalException("挂号记录不存在");
        }

        medicalRegistrationDao.updateRegistrationStatus(registrationId, -1);
        medicalRegistrationDao.decreaseScheduleNum(MapUtil.getInt(registration, "doctorScheduleId"));
        return 1;
    }
}
