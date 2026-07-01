package com.hospital.hms.service.impl;

import cn.hutool.core.map.MapUtil;
import com.hospital.common.exception.GlobalException;
import com.hospital.hms.dao.MedicalRegistrationDao;
import com.hospital.hms.dao.PatientDao;
import com.hospital.hms.event.HmsDomainEvent;
import com.hospital.hms.event.HmsDomainEventPublisher;
import com.hospital.hms.event.RegistrationEventPayload;
import com.hospital.hms.pojo.MedicalRegistration;
import com.hospital.hms.service.MedicalRegistrationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.HashMap;
import java.util.UUID;

@Service
public class MedicalRegistrationServiceImpl implements MedicalRegistrationService {

    @Autowired
    private MedicalRegistrationDao medicalRegistrationDao;

    @Autowired
    private PatientDao patientDao;

    @Autowired
    private HmsDomainEventPublisher eventPublisher;

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
        eventPublisher.publishAfterCommit(buildRegistrationEvent("registration.created", entity.getId(), entity));
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
        MedicalRegistration entity = new MedicalRegistration();
        entity.setId(registrationId);
        entity.setPatientId(MapUtil.getInt(registration, "patientId"));
        entity.setWorkPlanId(MapUtil.getInt(registration, "workPlanId"));
        entity.setDoctorScheduleId(MapUtil.getInt(registration, "doctorScheduleId"));
        entity.setDoctorId(MapUtil.getInt(registration, "doctorId"));
        entity.setDeptSubId(MapUtil.getInt(registration, "deptSubId"));
        entity.setDate(MapUtil.getStr(registration, "date"));
        entity.setSlot(MapUtil.getInt(registration, "slot"));
        medicalRegistrationDao.decreaseScheduleNum(MapUtil.getInt(registration, "doctorScheduleId"));
        eventPublisher.publishAfterCommit(buildRegistrationEvent("registration.cancelled", registrationId, entity));
        return 1;
    }

    private HmsDomainEvent<RegistrationEventPayload> buildRegistrationEvent(
            String eventType, Integer registrationId, MedicalRegistration entity) {
        return new HmsDomainEvent<>(
                UUID.randomUUID().toString(),
                eventType,
                Instant.now(),
                UUID.randomUUID().toString(),
                "system",
                null,
                new RegistrationEventPayload(
                        registrationId,
                        entity.getPatientId(),
                        entity.getWorkPlanId(),
                        entity.getDoctorScheduleId(),
                        entity.getDoctorId(),
                        entity.getDeptSubId(),
                        entity.getDate(),
                        entity.getSlot()
                )
        );
    }
}
