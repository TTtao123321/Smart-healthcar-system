package com.hospital.hms.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.InsertMedicalRecordForm;
import com.hospital.hms.controller.form.SearchMedicalRecordForm;
import com.hospital.hms.controller.form.UpdateMedicalRecordForm;
import com.hospital.hms.pojo.MedicalRecord;
import com.hospital.hms.service.MedicalRecordService;
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
 * MedicalRecordController 单元测试
 * 使用纯 Mockito 测试，不依赖 Spring Context
 */
@ExtendWith(MockitoExtension.class)
public class MedicalRecordControllerTest {

    @InjectMocks
    private MedicalRecordController medicalRecordController;

    @Mock
    private MedicalRecordService medicalRecordService;

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
            InsertMedicalRecordForm form = new InsertMedicalRecordForm();
            form.setRegistrationId(1);
            form.setPatientId(1);
            form.setDoctorId(1);
            form.setDeptSubId(10);
            form.setChiefComplaint("头痛发热");
            form.setPresentIllness("三天前开始头痛");
            form.setPhysicalExam("体温38.5度");
            form.setDiagnosis("上呼吸道感染");
            form.setDoctorAdvice("多喝水注意休息");
            form.setRemark("无");

            when(medicalRecordService.insertMedicalRecord(any(MedicalRecord.class))).thenReturn(1);

            CommonResult result = medicalRecordController.insert(form);

            assertEquals(200, result.get("code"));
            assertEquals("success", result.get("msg"));
            assertEquals(1, result.get("result"));
        }
    }

    @Test
    @DisplayName("insert_异常返回错误")
    void insert_异常返回错误() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertMedicalRecordForm form = new InsertMedicalRecordForm();
            form.setRegistrationId(1);
            form.setPatientId(1);
            form.setDoctorId(1);
            form.setChiefComplaint("头痛发热");

            when(medicalRecordService.insertMedicalRecord(any(MedicalRecord.class)))
                    .thenThrow(new RuntimeException("数据库异常"));

            CommonResult result = medicalRecordController.insert(form);

            assertEquals(500, result.get("code"));
            assertEquals("添加失败！", result.get("msg"));
        }
    }

    // ==================== update 接口测试 ====================

    @Test
    @DisplayName("update_正常返回成功")
    void update_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            UpdateMedicalRecordForm form = new UpdateMedicalRecordForm();
            form.setId(1);
            form.setChiefComplaint("头痛加重");
            form.setPresentIllness("五天前开始头痛");
            form.setPhysicalExam("体温39度");
            form.setDiagnosis("流感");
            form.setDoctorAdvice("服用退烧药");
            form.setRemark("复查");

            when(medicalRecordService.updateMedicalRecord(any(MedicalRecord.class))).thenReturn(1);

            CommonResult result = medicalRecordController.update(form);

            assertEquals(200, result.get("code"));
            assertEquals("success", result.get("msg"));
            assertEquals(1, result.get("result"));
        }
    }

    @Test
    @DisplayName("update_异常返回错误")
    void update_异常返回错误() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            UpdateMedicalRecordForm form = new UpdateMedicalRecordForm();
            form.setId(1);
            form.setDiagnosis("支气管炎");

            when(medicalRecordService.updateMedicalRecord(any(MedicalRecord.class)))
                    .thenThrow(new RuntimeException("数据库异常"));

            CommonResult result = medicalRecordController.update(form);

            assertEquals(500, result.get("code"));
            assertEquals("修改失败！", result.get("msg"));
        }
    }

    // ==================== selectById 接口测试 ====================

    @Test
    @DisplayName("selectById_正常返回病历")
    void selectById_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            MedicalRecord record = new MedicalRecord();
            record.setId(1);
            record.setUuid("abc123");
            record.setRegistrationId(1);
            record.setPatientId(1);
            record.setDoctorId(1);
            record.setChiefComplaint("头痛发热");
            record.setDiagnosis("上呼吸道感染");

            when(medicalRecordService.selectById(1)).thenReturn(record);

            Map<String, Integer> param = new HashMap<>();
            param.put("id", 1);

            CommonResult result = medicalRecordController.selectById(param);

            assertEquals(200, result.get("code"));
            MedicalRecord resultRecord = (MedicalRecord) result.get("result");
            assertNotNull(resultRecord);
            assertEquals(1, resultRecord.getId());
            assertEquals("头痛发热", resultRecord.getChiefComplaint());
            assertEquals("上呼吸道感染", resultRecord.getDiagnosis());
        }
    }

    @Test
    @DisplayName("selectById_不存在返回null")
    void selectById_不存在返回null() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            when(medicalRecordService.selectById(999)).thenReturn(null);

            Map<String, Integer> param = new HashMap<>();
            param.put("id", 999);

            CommonResult result = medicalRecordController.selectById(param);

            assertEquals(200, result.get("code"));
            assertNull(result.get("result"));
        }
    }

    @Test
    @DisplayName("selectById_异常返回错误")
    void selectById_异常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            when(medicalRecordService.selectById(1))
                    .thenThrow(new RuntimeException("查询异常"));

            Map<String, Integer> param = new HashMap<>();
            param.put("id", 1);

            CommonResult result = medicalRecordController.selectById(param);

            assertEquals(500, result.get("code"));
            assertEquals("查询失败！", result.get("msg"));
        }
    }

    // ==================== selectByRegistrationId 接口测试 ====================

    @Test
    @DisplayName("selectByRegistrationId_正常返回病历")
    void selectByRegistrationId_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            MedicalRecord record = new MedicalRecord();
            record.setId(1);
            record.setRegistrationId(10);
            record.setPatientId(2);
            record.setDoctorId(3);
            record.setChiefComplaint("咳嗽");
            record.setDiagnosis("支气管炎");

            when(medicalRecordService.selectByRegistrationId(10)).thenReturn(record);

            Map<String, Integer> param = new HashMap<>();
            param.put("registrationId", 10);

            CommonResult result = medicalRecordController.selectByRegistrationId(param);

            assertEquals(200, result.get("code"));
            MedicalRecord resultRecord = (MedicalRecord) result.get("result");
            assertNotNull(resultRecord);
            assertEquals(10, resultRecord.getRegistrationId());
            assertEquals("咳嗽", resultRecord.getChiefComplaint());
        }
    }

    @Test
    @DisplayName("selectByRegistrationId_无关联返回null")
    void selectByRegistrationId_无关联返回null() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            when(medicalRecordService.selectByRegistrationId(999)).thenReturn(null);

            Map<String, Integer> param = new HashMap<>();
            param.put("registrationId", 999);

            CommonResult result = medicalRecordController.selectByRegistrationId(param);

            assertEquals(200, result.get("code"));
            assertNull(result.get("result"));
        }
    }

    // ==================== selectByPage 接口测试 ====================

    @Test
    @DisplayName("selectByPage_正常返回分页数据")
    void selectByPage_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            SearchMedicalRecordForm form = new SearchMedicalRecordForm();
            form.setPatientId(5);
            form.setPage(1);
            form.setLength(10);

            ArrayList<MedicalRecord> list = new ArrayList<>();
            MedicalRecord record = new MedicalRecord();
            record.setId(1);
            record.setPatientId(5);
            record.setChiefComplaint("发热");
            list.add(record);

            PageUtils pageUtils = new PageUtils(list, 1, 1, 10);
            when(medicalRecordService.selectByPage(anyMap())).thenReturn(pageUtils);

            CommonResult result = medicalRecordController.selectByPage(form);

            assertEquals(200, result.get("code"));
            assertNotNull(result.get("result"));
        }
    }

    @Test
    @DisplayName("selectByPage_异常返回错误")
    void selectByPage_异常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            SearchMedicalRecordForm form = new SearchMedicalRecordForm();
            form.setPage(1);
            form.setLength(10);

            when(medicalRecordService.selectByPage(anyMap()))
                    .thenThrow(new RuntimeException("查询异常"));

            CommonResult result = medicalRecordController.selectByPage(form);

            assertEquals(500, result.get("code"));
            assertEquals("查询失败！", result.get("msg"));
        }
    }
}
