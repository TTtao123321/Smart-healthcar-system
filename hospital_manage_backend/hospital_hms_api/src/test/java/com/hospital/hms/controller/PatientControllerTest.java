package com.hospital.hms.controller;

import cn.dev33.satoken.stp.StpUtil;
import cn.hutool.core.bean.BeanUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.InsertPatientUserInfoForm;
import com.hospital.hms.controller.form.SelectPatientByPageForm;
import com.hospital.hms.controller.form.SelectPatientRegistrationsForm;
import com.hospital.hms.controller.form.UpdatePatientForm;
import com.hospital.hms.pojo.PatientUserInfo;
import com.hospital.hms.service.PatientService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * PatientController 单元测试
 * 使用纯 Mockito 测试，不依赖 Spring Context
 */
@ExtendWith(MockitoExtension.class)
public class PatientControllerTest {

    @InjectMocks
    private PatientController patientController;

    @Mock
    private PatientService patientService;

    private ObjectMapper objectMapper = new ObjectMapper();

    /**
     * 模拟 Sa-Token 登录态的辅助方法
     * 使用 try-with-resources 确保 MockedStatic 在测试后关闭
     */
    private MockedStatic<StpUtil> mockSaTokenLogin() {
        MockedStatic<StpUtil> stpUtilMock = mockStatic(StpUtil.class);
        stpUtilMock.when(StpUtil::isLogin).thenReturn(true);
        stpUtilMock.when(() -> StpUtil.hasPermission(anyString())).thenReturn(true);
        stpUtilMock.when(StpUtil::getLoginIdAsInt).thenReturn(1);
        return stpUtilMock;
    }

    // ==================== insert 接口测试 ====================

    @Test
    @DisplayName("insert_正常 - 合法参数返回成功")
    void insert_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertPatientUserInfoForm form = new InsertPatientUserInfoForm();
            form.setName("张三丰");
            form.setSex("男");
            form.setPid("110101199001011234");
            form.setTel("13800138000");
            form.setBirthday("1990-01-01");
            form.setMedicalHistory("无");
            form.setAllergyHistory("无");
            form.setFamilyHistory("无");
            form.setInsuranceType(1);

            when(patientService.insertPatient(any(PatientUserInfo.class))).thenReturn(1);

            CommonResult result = patientController.insert(form);

            assertEquals(200, result.get("code"));
            assertEquals("success", result.get("msg"));
            assertEquals(1, result.get("result"));
        }
    }

    @Test
    @DisplayName("insert_可选字段不传也能成功")
    void insert_可选字段不传() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertPatientUserInfoForm form = new InsertPatientUserInfoForm();
            form.setName("李四五");
            form.setSex("女");
            form.setPid("110101199002021234");
            form.setTel("13900139000");
            form.setBirthday("1990-02-02");
            // medicalHistory/allergyHistory/familyHistory/insuranceType 不传

            when(patientService.insertPatient(any(PatientUserInfo.class))).thenReturn(1);

            CommonResult result = patientController.insert(form);

            assertEquals(200, result.get("code"));
            assertEquals(1, result.get("result"));
        }
    }

    @Test
    @DisplayName("insert_异常时返回错误")
    void insert_异常返回错误() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertPatientUserInfoForm form = new InsertPatientUserInfoForm();
            form.setName("测试");
            form.setSex("男");
            form.setPid("110101199001011234");
            form.setTel("13800138000");
            form.setBirthday("1990-01-01");

            when(patientService.insertPatient(any(PatientUserInfo.class)))
                    .thenThrow(new RuntimeException("数据库异常"));

            CommonResult result = patientController.insert(form);

            assertEquals(500, result.get("code"));
            assertEquals("添加失败！", result.get("msg"));
        }
    }

    // ==================== update 接口测试 ====================

    @Test
    @DisplayName("update_正常返回成功")
    void update_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            UpdatePatientForm form = new UpdatePatientForm();
            form.setId(1);
            form.setName("王五六");
            form.setTel("13700137000");

            when(patientService.updatePatient(any(PatientUserInfo.class))).thenReturn(1);

            CommonResult result = patientController.update(form);

            assertEquals(200, result.get("code"));
            assertEquals(1, result.get("result"));
        }
    }

    @Test
    @DisplayName("update_异常时返回错误")
    void update_异常返回错误() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            UpdatePatientForm form = new UpdatePatientForm();
            form.setId(1);
            form.setName("测试");

            when(patientService.updatePatient(any(PatientUserInfo.class)))
                    .thenThrow(new RuntimeException("数据库异常"));

            CommonResult result = patientController.update(form);

            assertEquals(500, result.get("code"));
            assertEquals("修改失败！", result.get("msg"));
        }
    }

    // ==================== selectByPage 接口测试 ====================

    @Test
    @DisplayName("selectByPage_正常返回分页数据")
    void selectByPage_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            SelectPatientByPageForm form = new SelectPatientByPageForm();
            form.setPage(1);
            form.setLength(10);

            PageUtils pageUtils = new PageUtils(new ArrayList<>(), 0L, 1, 10);
            when(patientService.selectPatientByPage(anyMap())).thenReturn(pageUtils);

            CommonResult result = patientController.selectByPage(form);

            assertEquals(200, result.get("code"));
            assertNotNull(result.get("result"));
        }
    }

    @Test
    @DisplayName("selectByPage_异常时返回错误")
    void selectByPage_异常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            SelectPatientByPageForm form = new SelectPatientByPageForm();
            form.setPage(1);
            form.setLength(10);

            when(patientService.selectPatientByPage(anyMap()))
                    .thenThrow(new RuntimeException("查询异常"));

            CommonResult result = patientController.selectByPage(form);

            assertEquals(500, result.get("code"));
            assertEquals("查询失败！", result.get("msg"));
        }
    }

    // ==================== selectDetail 接口测试 ====================

    @Test
    @DisplayName("selectDetail_正常返回详情")
    void selectDetail_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            SelectPatientRegistrationsForm form = new SelectPatientRegistrationsForm();
            form.setPatientCardId(1);

            HashMap<String, Object> detail = new HashMap<>();
            detail.put("name", "张三丰");
            detail.put("sex", "男");
            when(patientService.selectPatientDetail(1, null, null)).thenReturn(detail);

            CommonResult result = patientController.selectDetail(form);

            assertEquals(200, result.get("code"));
        }
    }

    @Test
    @DisplayName("selectDetail_异常时返回错误")
    void selectDetail_异常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            SelectPatientRegistrationsForm form = new SelectPatientRegistrationsForm();
            form.setPatientCardId(1);

            when(patientService.selectPatientDetail(1, null, null))
                    .thenThrow(new RuntimeException("查询异常"));

            CommonResult result = patientController.selectDetail(form);

            assertEquals(500, result.get("code"));
            assertEquals("查询失败！", result.get("msg"));
        }
    }
}
