package com.hospital.hms.service;

import com.hospital.hms.dao.PatientDao;
import com.hospital.hms.service.impl.PatientResultServiceImpl;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.HashMap;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PatientResultServiceImplTest {

    @Mock
    private PatientDao patientDao;

    @InjectMocks
    private PatientResultServiceImpl patientResultService;

    @Test
    @DisplayName("selectPatientMedicalRecordDetail_仅返回患者可见字段")
    void selectPatientMedicalRecordDetail_仅返回患者可见字段() {
        HashMap<String, Object> row = new HashMap<>();
        row.put("medicalRecordId", 101);
        row.put("visitDate", "2026-07-01");
        row.put("department", "呼吸内科");
        row.put("doctorName", "张医生");
        row.put("chiefComplaint", "咳嗽 3 天");
        row.put("presentIllness", "夜间加重，伴低热");
        row.put("physicalExam", "双肺呼吸音粗");
        row.put("diagnosis", "上呼吸道感染");
        row.put("doctorAdvice", "清淡饮食，医生内部备注：复诊时复查血常规");
        row.put("remark", "仅医生查看");
        when(patientDao.selectPatientMedicalRecordDetail(7, 101)).thenReturn(row);

        HashMap<String, Object> result = patientResultService.selectPatientMedicalRecordDetail(7, 101);

        assertEquals(101, result.get("medicalRecordId"));
        assertEquals("2026-07-01", result.get("visitDate"));
        assertEquals("呼吸内科", result.get("department"));
        assertEquals("张医生", result.get("doctorName"));
        assertEquals("咳嗽 3 天", result.get("chiefComplaint"));
        assertEquals("上呼吸道感染", result.get("diagnosisSummary"));
        assertEquals("清淡饮食", result.get("instructionSummary"));
        assertFalse(result.containsKey("presentIllness"));
        assertFalse(result.containsKey("physicalExam"));
        assertFalse(result.containsKey("remark"));
        assertFalse(result.containsKey("doctorAdvice"));
    }

    @Test
    @DisplayName("selectPatientPrescriptionDetail_隐藏医生内部备注")
    void selectPatientPrescriptionDetail_隐藏医生内部备注() {
        HashMap<String, Object> row = new HashMap<>();
        row.put("prescriptionId", 88);
        row.put("doctorAdvice", "口服，每日三次，医生内部备注：术后随访");
        when(patientDao.selectPatientPrescriptionDetail(7, 88)).thenReturn(row);

        HashMap<String, Object> result = patientResultService.selectPatientPrescriptionDetail(7, 88);

        assertEquals("口服，每日三次", result.get("doctorAdvice"));
    }
}
