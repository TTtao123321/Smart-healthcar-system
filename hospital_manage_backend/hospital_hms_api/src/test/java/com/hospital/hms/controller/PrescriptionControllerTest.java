package com.hospital.hms.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.InsertPrescriptionForm;
import com.hospital.hms.pojo.PrescriptionItem;
import com.hospital.hms.service.PrescriptionService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * PrescriptionController 单元测试
 * 使用纯 Mockito 测试，不依赖 Spring Context
 */
@ExtendWith(MockitoExtension.class)
public class PrescriptionControllerTest {

    @InjectMocks
    private PrescriptionController prescriptionController;

    @Mock
    private PrescriptionService prescriptionService;

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
    @DisplayName("insert_正常含明细 - 西药类型返回成功")
    void insert_正常含明细() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertPrescriptionForm form = new InsertPrescriptionForm();
            form.setMedicalRecordId(1);
            form.setPatientId(10);
            form.setDoctorId(100);
            form.setType(0); // 西药

            InsertPrescriptionForm.PrescriptionItemForm item = new InsertPrescriptionForm.PrescriptionItemForm();
            item.setDrugName("阿莫西林");
            item.setSpecification("0.5g*24片");
            item.setQuantity(2);
            item.setDosage("每次1片");
            item.setFrequency("每日3次");
            item.setDays(7);
            item.setRemark("饭后服用");
            form.setItems(Collections.singletonList(item));

            when(prescriptionService.insertPrescription(any(), anyList())).thenReturn(1);

            CommonResult result = prescriptionController.insert(form);

            assertEquals(200, result.get("code"));
            assertEquals("success", result.get("msg"));
            assertEquals(1, result.get("result"));
        }
    }

    @Test
    @DisplayName("insert_中药类型也能成功")
    void insert_中药类型() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertPrescriptionForm form = new InsertPrescriptionForm();
            form.setMedicalRecordId(1);
            form.setPatientId(10);
            form.setDoctorId(100);
            form.setType(1); // 中药

            InsertPrescriptionForm.PrescriptionItemForm item = new InsertPrescriptionForm.PrescriptionItemForm();
            item.setDrugName("当归");
            item.setSpecification("500g");
            item.setQuantity(1);
            item.setDosage("10g");
            item.setFrequency("每日2次");
            item.setDays(14);
            item.setRemark("水煎服");
            form.setItems(Collections.singletonList(item));

            when(prescriptionService.insertPrescription(any(), anyList())).thenReturn(1);

            CommonResult result = prescriptionController.insert(form);

            assertEquals(200, result.get("code"));
            assertEquals(1, result.get("result"));
        }
    }

    @Test
    @DisplayName("insert_异常返回错误")
    void insert_异常返回错误() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            InsertPrescriptionForm form = new InsertPrescriptionForm();
            form.setMedicalRecordId(1);
            form.setPatientId(10);
            form.setDoctorId(100);
            form.setType(0);

            InsertPrescriptionForm.PrescriptionItemForm item = new InsertPrescriptionForm.PrescriptionItemForm();
            item.setDrugName("阿莫西林");
            form.setItems(Collections.singletonList(item));

            when(prescriptionService.insertPrescription(any(), anyList()))
                    .thenThrow(new RuntimeException("数据库异常"));

            CommonResult result = prescriptionController.insert(form);

            assertEquals(500, result.get("code"));
            assertEquals("添加失败！", result.get("msg"));
        }
    }

    // ==================== updateStatus 接口测试 ====================

    @Test
    @DisplayName("updateStatus_正常待取药转已取药")
    void updateStatus_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            Map<String, Integer> param = new HashMap<>();
            param.put("id", 1);
            param.put("status", 1); // 已取药

            when(prescriptionService.updatePrescriptionStatus(1, 1)).thenReturn(1);

            CommonResult result = prescriptionController.updateStatus(param);

            assertEquals(200, result.get("code"));
            assertEquals(1, result.get("result"));
        }
    }

    @Test
    @DisplayName("updateStatus_异常返回错误")
    void updateStatus_异常返回错误() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            Map<String, Integer> param = new HashMap<>();
            param.put("id", 1);
            param.put("status", 1);

            when(prescriptionService.updatePrescriptionStatus(1, 1))
                    .thenThrow(new RuntimeException("数据库异常"));

            CommonResult result = prescriptionController.updateStatus(param);

            assertEquals(500, result.get("code"));
            assertEquals("更新失败！", result.get("msg"));
        }
    }

    // ==================== selectByMedicalRecordId 接口测试 ====================

    @Test
    @DisplayName("selectByMedicalRecordId_正常返回处方列表")
    void selectByMedicalRecordId_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            Map<String, Integer> param = new HashMap<>();
            param.put("medicalRecordId", 1);

            ArrayList<Map<String, Object>> mockList = new ArrayList<>();
            Map<String, Object> record = new HashMap<>();
            record.put("id", 1);
            record.put("uuid", "abc123");
            record.put("medicalRecordId", 1);
            record.put("status", 0);
            mockList.add(record);

            when(prescriptionService.selectByMedicalRecordId(1)).thenReturn(mockList);

            CommonResult result = prescriptionController.selectByMedicalRecordId(param);

            assertEquals(200, result.get("code"));
            assertNotNull(result.get("result"));
        }
    }

    @Test
    @DisplayName("selectByMedicalRecordId_无数据返回空列表")
    void selectByMedicalRecordId_无数据() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            Map<String, Integer> param = new HashMap<>();
            param.put("medicalRecordId", 999);

            when(prescriptionService.selectByMedicalRecordId(999)).thenReturn(new ArrayList<>());

            CommonResult result = prescriptionController.selectByMedicalRecordId(param);

            assertEquals(200, result.get("code"));
            assertNotNull(result.get("result"));
        }
    }

    // ==================== selectItemsByPrescriptionId 接口测试 ====================

    @Test
    @DisplayName("selectItemsByPrescriptionId_正常返回明细列表")
    void selectItemsByPrescriptionId_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            Map<String, Integer> param = new HashMap<>();
            param.put("prescriptionId", 1);

            PrescriptionItem item = new PrescriptionItem();
            item.setId(1);
            item.setPrescriptionId(1);
            item.setDrugName("阿莫西林");
            item.setSpecification("0.5g*24片");
            item.setQuantity(2);
            item.setDosage("每次1片");
            item.setFrequency("每日3次");
            item.setDays(7);
            item.setRemark("饭后服用");

            when(prescriptionService.selectItemsByPrescriptionId(1)).thenReturn(Collections.singletonList(item));

            CommonResult result = prescriptionController.selectItemsByPrescriptionId(param);

            assertEquals(200, result.get("code"));
            assertNotNull(result.get("result"));
        }
    }

    @Test
    @DisplayName("selectItemsByPrescriptionId_无数据返回空列表")
    void selectItemsByPrescriptionId_无数据() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            Map<String, Integer> param = new HashMap<>();
            param.put("prescriptionId", 999);

            when(prescriptionService.selectItemsByPrescriptionId(999)).thenReturn(new ArrayList<>());

            CommonResult result = prescriptionController.selectItemsByPrescriptionId(param);

            assertEquals(200, result.get("code"));
            assertNotNull(result.get("result"));
        }
    }

    // ==================== selectByPatientId 接口测试 ====================

    @Test
    @DisplayName("selectByPatientId_正常返回分页数据")
    void selectByPatientId_正常() {
        try (MockedStatic<StpUtil> ignored = mockSaTokenLogin()) {
            Map<String, Object> param = new HashMap<>();
            param.put("patientId", 10);
            param.put("page", 1);
            param.put("length", 10);

            ArrayList<Map<String, Object>> list = new ArrayList<>();
            Map<String, Object> record = new HashMap<>();
            record.put("id", 1);
            record.put("patientId", 10);
            record.put("status", 0);
            list.add(record);

            PageUtils pageUtils = new PageUtils(list, 1, 1, 10);
            when(prescriptionService.selectByPatientId(anyMap())).thenReturn(pageUtils);

            CommonResult result = prescriptionController.selectByPatientId(param);

            assertEquals(200, result.get("code"));
            assertNotNull(result.get("result"));
        }
    }
}
