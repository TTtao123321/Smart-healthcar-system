package com.hospital.hms.controller;

import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.SelectPatientMedicalRecordsForm;
import com.hospital.hms.service.PatientResultService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.HashMap;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PatientResultControllerTest {

    @InjectMocks
    private PatientResultController patientResultController;

    @Mock
    private PatientResultService patientResultService;

    @Test
    @DisplayName("selectMedicalRecords_正常返回患者病历列表")
    void selectMedicalRecords_正常返回患者病历列表() {
        SelectPatientMedicalRecordsForm form = new SelectPatientMedicalRecordsForm();
        form.setPatientId(7);

        HashMap<String, Object> item = new HashMap<>();
        item.put("medicalRecordId", 101);
        item.put("visitDate", "2026-07-01");
        item.put("doctorName", "张医生");
        when(patientResultService.selectPatientMedicalRecords(7, null, null)).thenReturn(List.of(item));

        CommonResult result = patientResultController.selectMedicalRecords(form);

        assertEquals(200, result.get("code"));
        assertEquals(101, ((List<?>) result.get("result")).stream()
                .map(entry -> ((HashMap<?, ?>) entry).get("medicalRecordId"))
                .findFirst()
                .orElse(null));
        verify(patientResultService).selectPatientMedicalRecords(7, null, null);
    }
}
