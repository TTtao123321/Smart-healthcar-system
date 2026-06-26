package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.PatientDao;
import com.hospital.hms.pojo.PatientUserInfo;
import com.hospital.hms.service.impl.PatientServiceImpl;
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
 * PatientServiceImpl 单元测试
 */
@ExtendWith(MockitoExtension.class)
public class PatientServiceImplTest {

    @Mock
    private PatientDao patientDao;

    @InjectMocks
    private PatientServiceImpl patientService;

    // ==================== insertPatient 测试 ====================

    @Test
    @DisplayName("insertPatient_正常 - mock dao返回1，验证调用")
    void insertPatient_正常() {
        // 准备数据
        PatientUserInfo patient = new PatientUserInfo();
        patient.setName("张三丰");
        patient.setSex("男");
        patient.setPid("110101199001011234");

        // mock dao返回1
        when(patientDao.insertPatient(any(PatientUserInfo.class))).thenReturn(1);

        // 执行
        int result = patientService.insertPatient(patient);

        // 验证返回值
        assertEquals(1, result);
        // 验证dao被调用
        verify(patientDao, times(1)).insertPatient(patient);
    }

    @Test
    @DisplayName("insertPatient_返回受影响行数 - 验证返回值")
    void insertPatient_返回受影响行数() {
        PatientUserInfo patient = new PatientUserInfo();
        patient.setName("李四五");

        // mock dao返回2（模拟受影响行数）
        when(patientDao.insertPatient(any(PatientUserInfo.class))).thenReturn(2);

        int result = patientService.insertPatient(patient);

        assertEquals(2, result);
        verify(patientDao).insertPatient(patient);
    }

    // ==================== updatePatient 测试 ====================

    @Test
    @DisplayName("updatePatient_正常 - mock dao返回1")
    void updatePatient_正常() {
        PatientUserInfo patient = new PatientUserInfo();
        patient.setId(1);
        patient.setName("王五六");

        when(patientDao.updatePatientById(any(PatientUserInfo.class))).thenReturn(1);

        int result = patientService.updatePatient(patient);

        assertEquals(1, result);
        verify(patientDao).updatePatientById(patient);
    }

    // ==================== selectPatientDetail 测试 ====================

    @Test
    @DisplayName("selectPatientDetail_正常 - mock两个dao方法，验证result包含patientInfo和registrations")
    void selectPatientDetail_正常() {
        Integer patientId = 1;
        Integer deptSubId = 2;
        Integer doctorId = 3;

        // mock 患者信息
        HashMap<String, Object> patientInfo = new HashMap<>();
        patientInfo.put("patientId", 1);
        patientInfo.put("name", "张三丰");
        patientInfo.put("sex", "男");
        when(patientDao.selectPatientInfoById(patientId)).thenReturn(patientInfo);

        // mock 挂号记录
        HashMap<String, Object> registration = new HashMap<>();
        registration.put("registrationId", 100);
        registration.put("deptName", "内科");
        List<HashMap<String, Object>> registrations = new ArrayList<>();
        registrations.add(registration);
        when(patientDao.selectRegistrationsByPatientId(anyMap())).thenReturn(registrations);

        // 执行
        HashMap<String, Object> result = patientService.selectPatientDetail(patientId, deptSubId, doctorId);

        // 验证结果包含patientInfo和registrations
        assertNotNull(result);
        assertSame(patientInfo, result.get("patientInfo"));
        assertSame(registrations, result.get("registrations"));
        assertEquals(1, ((HashMap<String, Object>) result.get("patientInfo")).get("patientId"));
        verify(patientDao).selectPatientInfoById(patientId);
        verify(patientDao).selectRegistrationsByPatientId(anyMap());
    }

    @Test
    @DisplayName("selectPatientDetail_患者不存在 - dao返回null，验证不抛异常")
    void selectPatientDetail_患者不存在() {
        Integer patientId = 999;

        // mock dao返回null
        when(patientDao.selectPatientInfoById(patientId)).thenReturn(null);
        when(patientDao.selectRegistrationsByPatientId(anyMap())).thenReturn(new ArrayList<>());

        // 执行，验证不抛异常
        HashMap<String, Object> result = assertDoesNotThrow(() -> patientService.selectPatientDetail(patientId, null, null));

        // 验证结果中patientInfo为null
        assertNotNull(result);
        assertNull(result.get("patientInfo"));
        assertNotNull(result.get("registrations"));
    }

    // ==================== selectPatientByPage 测试 ====================

    @Test
    @DisplayName("selectPatientByPage_正常 - mock count和list，验证PageUtils字段")
    void selectPatientByPage_正常() {
        // 准备分页参数
        Map<String, Object> map = new HashMap<>();
        map.put("page", 2);
        map.put("length", 10);

        // mock 总数
        when(patientDao.selectPatientByPageCount(map)).thenReturn(25L);

        // mock 列表数据
        HashMap<String, Object> patient1 = new HashMap<>();
        patient1.put("name", "张三");
        List<HashMap<String, Object>> list = new ArrayList<>();
        list.add(patient1);
        when(patientDao.selectPatientByPage(map)).thenReturn(list);

        // 执行
        PageUtils result = patientService.selectPatientByPage(map);

        // 验证PageUtils字段
        assertNotNull(result);
        assertEquals(25L, result.getTotalCount());
        assertEquals(2, result.getPageIndex());
        assertEquals(10, result.getPageSize());
        assertEquals(3, result.getTotalPage()); // 25/10=2.5，向上取整为3
        assertEquals(list, result.getList());

        // 验证start被正确计算并放入map中: (2-1)*10=10
        assertEquals(10, map.get("start"));

        verify(patientDao).selectPatientByPageCount(map);
        verify(patientDao).selectPatientByPage(map);
    }
}
