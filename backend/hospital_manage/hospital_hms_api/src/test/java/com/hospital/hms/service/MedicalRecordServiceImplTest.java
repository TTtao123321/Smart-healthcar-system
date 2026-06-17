package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.MedicalRecordDao;
import com.hospital.hms.pojo.MedicalRecord;
import com.hospital.hms.service.impl.MedicalRecordServiceImpl;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * MedicalRecordServiceImpl 单元测试
 */
@ExtendWith(MockitoExtension.class)
public class MedicalRecordServiceImplTest {

    @Mock
    private MedicalRecordDao medicalRecordDao;

    @InjectMocks
    private MedicalRecordServiceImpl medicalRecordService;

    // ==================== insertMedicalRecord 测试 ====================

    @Test
    @DisplayName("insertMedicalRecord_正常")
    void insertMedicalRecord_正常() {
        MedicalRecord record = new MedicalRecord();
        record.setRegistrationId(1);
        record.setPatientId(100);
        record.setChiefComplaint("头痛");

        when(medicalRecordDao.insert(any(MedicalRecord.class))).thenReturn(1);

        int result = medicalRecordService.insertMedicalRecord(record);

        assertEquals(1, result);
        verify(medicalRecordDao).insert(record);
    }

    // ==================== updateMedicalRecord 测试 ====================

    @Test
    @DisplayName("updateMedicalRecord_正常")
    void updateMedicalRecord_正常() {
        MedicalRecord record = new MedicalRecord();
        record.setId(1);
        record.setDiagnosis("感冒");

        when(medicalRecordDao.updateById(any(MedicalRecord.class))).thenReturn(1);

        int result = medicalRecordService.updateMedicalRecord(record);

        assertEquals(1, result);
        verify(medicalRecordDao).updateById(record);
    }

    // ==================== selectById 测试 ====================

    @Test
    @DisplayName("selectById_存在 - mock返回MedicalRecord对象")
    void selectById_存在() {
        Integer id = 1;
        MedicalRecord record = new MedicalRecord();
        record.setId(id);
        record.setDiagnosis("感冒");

        when(medicalRecordDao.selectById(id)).thenReturn(record);

        MedicalRecord result = medicalRecordService.selectById(id);

        assertNotNull(result);
        assertEquals(id, result.getId());
        assertEquals("感冒", result.getDiagnosis());
        verify(medicalRecordDao).selectById(id);
    }

    @Test
    @DisplayName("selectById_不存在 - mock返回null")
    void selectById_不存在() {
        Integer id = 999;

        when(medicalRecordDao.selectById(id)).thenReturn(null);

        MedicalRecord result = medicalRecordService.selectById(id);

        assertNull(result);
        verify(medicalRecordDao).selectById(id);
    }

    // ==================== selectByRegistrationId 测试 ====================

    @Test
    @DisplayName("selectByRegistrationId_存在")
    void selectByRegistrationId_存在() {
        Integer registrationId = 10;
        MedicalRecord record = new MedicalRecord();
        record.setId(1);
        record.setRegistrationId(registrationId);

        when(medicalRecordDao.selectByRegistrationId(registrationId)).thenReturn(record);

        MedicalRecord result = medicalRecordService.selectByRegistrationId(registrationId);

        assertNotNull(result);
        assertEquals(registrationId, result.getRegistrationId());
        verify(medicalRecordDao).selectByRegistrationId(registrationId);
    }

    @Test
    @DisplayName("selectByRegistrationId_不存在")
    void selectByRegistrationId_不存在() {
        Integer registrationId = 999;

        when(medicalRecordDao.selectByRegistrationId(registrationId)).thenReturn(null);

        MedicalRecord result = medicalRecordService.selectByRegistrationId(registrationId);

        assertNull(result);
        verify(medicalRecordDao).selectByRegistrationId(registrationId);
    }

    // ==================== selectByPage 测试 ====================

    @Test
    @DisplayName("selectByPage_正常 - 验证分页计算逻辑(start = (page-1)*length)")
    void selectByPage_正常() {
        // 准备分页参数
        Map<String, Object> map = new HashMap<>();
        map.put("page", 3);
        map.put("length", 10);

        // mock 总数
        when(medicalRecordDao.selectByPageCount(map)).thenReturn(55L);

        // mock 列表数据
        HashMap<String, Object> record1 = new HashMap<>();
        record1.put("id", 21);
        List<HashMap<String, Object>> list = new ArrayList<>();
        list.add(record1);
        when(medicalRecordDao.selectByPage(map)).thenReturn(list);

        // 执行
        PageUtils result = medicalRecordService.selectByPage(map);

        // 验证PageUtils字段
        assertNotNull(result);
        assertEquals(55L, result.getTotalCount());
        assertEquals(3, result.getPageIndex());
        assertEquals(10, result.getPageSize());
        assertEquals(6, result.getTotalPage()); // 55/10=5.5，向上取整为6
        assertEquals(list, result.getList());

        // 验证分页计算逻辑: start = (page-1)*length = (3-1)*10 = 20
        assertEquals(20, map.get("start"));

        verify(medicalRecordDao).selectByPageCount(map);
        verify(medicalRecordDao).selectByPage(map);
    }
}
