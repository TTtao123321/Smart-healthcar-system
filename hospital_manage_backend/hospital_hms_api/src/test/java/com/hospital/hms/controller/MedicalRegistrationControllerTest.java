package com.hospital.hms.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.InsertMedicalRegistrationForm;
import com.hospital.hms.service.MedicalRegistrationService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class MedicalRegistrationControllerTest {

    @InjectMocks
    private MedicalRegistrationController medicalRegistrationController;

    @Mock
    private MedicalRegistrationService medicalRegistrationService;

    private MockedStatic<StpUtil> mockSaTokenLogin() {
        MockedStatic<StpUtil> stpUtilMock = mockStatic(StpUtil.class);
        stpUtilMock.when(StpUtil::isLogin).thenReturn(true);
        stpUtilMock.when(() -> StpUtil.hasPermission(any())).thenReturn(true);
        stpUtilMock.when(StpUtil::getLoginIdAsInt).thenReturn(1);
        return stpUtilMock;
    }

    @Test
    @DisplayName("save_正常返回成功")
    void save_正常返回成功() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertMedicalRegistrationForm form = new InsertMedicalRegistrationForm();
            form.setPatientId(1);
            form.setWorkPlanId(10);
            form.setDoctorScheduleId(100);
            form.setDoctorId(8);
            form.setDeptSubId(3);
            form.setDate("2026-06-25");
            form.setSlot(1);

            when(medicalRegistrationService.save(any())).thenReturn(66);

            CommonResult result = medicalRegistrationController.save(form);

            assertEquals(200, result.get("code"));
            assertEquals(66, ((java.util.Map<?, ?>) result.get("result")).get("id"));
            assertEquals(0, ((java.util.Map<?, ?>) result.get("result")).get("status"));
        }
    }

    @Test
    @DisplayName("save_异常返回错误")
    void save_异常返回错误() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertMedicalRegistrationForm form = new InsertMedicalRegistrationForm();
            form.setPatientId(1);
            form.setWorkPlanId(10);
            form.setDoctorScheduleId(100);
            form.setDoctorId(8);
            form.setDeptSubId(3);
            form.setDate("2026-06-25");
            form.setSlot(1);

            when(medicalRegistrationService.save(any())).thenThrow(new RuntimeException("数据库异常"));

            CommonResult result = medicalRegistrationController.save(form);

            assertEquals(500, result.get("code"));
            assertEquals("挂号失败！", result.get("msg"));
        }
    }
}
