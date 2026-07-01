package com.hospital.hms.service;

import com.hospital.common.exception.GlobalException;
import com.hospital.hms.dao.MedicalRegistrationDao;
import com.hospital.hms.dao.PatientDao;
import com.hospital.hms.pojo.MedicalRegistration;
import com.hospital.hms.service.impl.MedicalRegistrationServiceImpl;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.HashMap;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class MedicalRegistrationServiceImplTest {

    @Mock
    private MedicalRegistrationDao medicalRegistrationDao;

    @Mock
    private PatientDao patientDao;

    @InjectMocks
    private MedicalRegistrationServiceImpl medicalRegistrationService;

    @Test
    @DisplayName("save_正常创建挂号并返回主键")
    void save_正常创建挂号并返回主键() {
        MedicalRegistration entity = new MedicalRegistration();
        entity.setPatientId(1);
        entity.setWorkPlanId(10);
        entity.setDoctorScheduleId(100);
        entity.setDoctorId(8);
        entity.setDeptSubId(3);
        entity.setDate("2026-06-25");
        entity.setSlot(1);

        HashMap<String, Object> patient = new HashMap<>();
        patient.put("id", 1);
        when(patientDao.selectPatientInfoById(1)).thenReturn(patient);

        HashMap<String, Object> schedule = new HashMap<>();
        schedule.put("maximum", 10);
        schedule.put("num", 3);
        schedule.put("workPlanStatus", "ACTIVE");
        when(medicalRegistrationDao.selectScheduleForUpdate(100)).thenReturn(schedule);
        doAnswer(invocation -> {
            MedicalRegistration arg = invocation.getArgument(0);
            arg.setId(66);
            return 1;
        }).when(medicalRegistrationDao).insert(any(MedicalRegistration.class));

        int id = medicalRegistrationService.save(entity);

        assertEquals(66, id);
        verify(medicalRegistrationDao).increaseScheduleNum(100);
    }

    @Test
    @DisplayName("save_号源已满时抛出异常")
    void save_号源已满时抛出异常() {
        MedicalRegistration entity = new MedicalRegistration();
        entity.setPatientId(1);
        entity.setDoctorScheduleId(100);

        HashMap<String, Object> patient = new HashMap<>();
        patient.put("id", 1);
        when(patientDao.selectPatientInfoById(1)).thenReturn(patient);

        HashMap<String, Object> schedule = new HashMap<>();
        schedule.put("maximum", 10);
        schedule.put("num", 10);
        schedule.put("workPlanStatus", "ACTIVE");
        when(medicalRegistrationDao.selectScheduleForUpdate(100)).thenReturn(schedule);

        assertThrows(GlobalException.class, () -> medicalRegistrationService.save(entity));
        verify(medicalRegistrationDao, never()).insert(any(MedicalRegistration.class));
    }

    @Test
    @DisplayName("save_加锁查询后号源已满时抛出异常")
    void save_加锁查询后号源已满时抛出异常() {
        MedicalRegistration entity = buildRegistration();

        HashMap<String, Object> patient = new HashMap<>();
        patient.put("id", 1);
        when(patientDao.selectPatientInfoById(1)).thenReturn(patient);

        HashMap<String, Object> schedule = new HashMap<>();
        schedule.put("maximum", 1);
        schedule.put("num", 1);
        schedule.put("workPlanStatus", "ACTIVE");
        when(medicalRegistrationDao.selectScheduleForUpdate(100)).thenReturn(schedule);

        assertThrows(GlobalException.class, () -> medicalRegistrationService.save(entity));
        verify(medicalRegistrationDao, never()).insert(any(MedicalRegistration.class));
    }

    @Test
    @DisplayName("cancelRegistration_取消挂号后回补号源")
    void cancelRegistration_取消挂号后回补号源() {
        HashMap<String, Object> registration = new HashMap<>();
        registration.put("doctorScheduleId", 100);
        when(medicalRegistrationDao.selectRegistrationById(66)).thenReturn(registration);

        int result = medicalRegistrationService.cancelRegistration(66);

        assertEquals(1, result);
        verify(medicalRegistrationDao).updateRegistrationStatus(66, -1);
        verify(medicalRegistrationDao).decreaseScheduleNum(100);
    }

    private MedicalRegistration buildRegistration() {
        MedicalRegistration entity = new MedicalRegistration();
        entity.setPatientId(1);
        entity.setWorkPlanId(10);
        entity.setDoctorScheduleId(100);
        entity.setDoctorId(8);
        entity.setDeptSubId(3);
        entity.setDate("2026-06-25");
        entity.setSlot(1);
        return entity;
    }
}
