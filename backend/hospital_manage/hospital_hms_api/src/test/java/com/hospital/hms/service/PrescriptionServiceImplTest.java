package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.PrescriptionDao;
import com.hospital.hms.dao.PrescriptionItemDao;
import com.hospital.hms.pojo.Prescription;
import com.hospital.hms.pojo.PrescriptionItem;
import com.hospital.hms.service.impl.PrescriptionServiceImpl;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * PrescriptionServiceImpl 单元测试
 */
@ExtendWith(MockitoExtension.class)
public class PrescriptionServiceImplTest {

    @Mock
    private PrescriptionDao prescriptionDao;

    @Mock
    private PrescriptionItemDao prescriptionItemDao;

    @InjectMocks
    private PrescriptionServiceImpl prescriptionService;

    // ==================== insertPrescription 测试 ====================

    @Test
    @DisplayName("insertPrescription_正常含明细 - 验证prescriptionDao.insert和prescriptionItemDao.batchInsert都被调用，且item的prescriptionId被正确设置")
    void insertPrescription_正常含明细() {
        // 准备处方主表数据
        Prescription prescription = new Prescription();
        prescription.setMedicalRecordId(1);
        prescription.setPatientId(100);
        prescription.setType(1);

        // 准备明细数据
        PrescriptionItem item1 = new PrescriptionItem();
        item1.setDrugName("阿莫西林");
        item1.setQuantity(2);

        PrescriptionItem item2 = new PrescriptionItem();
        item2.setDrugName("布洛芬");
        item2.setQuantity(1);

        List<PrescriptionItem> items = Arrays.asList(item1, item2);

        // mock prescriptionDao.insert，通过Answer模拟设置id
        when(prescriptionDao.insert(any(Prescription.class))).thenAnswer(invocation -> {
            Prescription p = invocation.getArgument(0);
            p.setId(50); // 模拟数据库自增id
            return 1;
        });

        // mock batchInsert
        when(prescriptionItemDao.batchInsert(anyList())).thenReturn(2);

        // 执行
        int result = prescriptionService.insertPrescription(prescription, items);

        // 验证返回值
        assertEquals(1, result);

        // 验证prescriptionDao.insert被调用
        verify(prescriptionDao).insert(prescription);

        // 验证每个item的prescriptionId被正确设置
        assertEquals(50, item1.getPrescriptionId());
        assertEquals(50, item2.getPrescriptionId());

        // 验证prescriptionItemDao.batchInsert被调用
        verify(prescriptionItemDao).batchInsert(items);
    }

    @Test
    @DisplayName("insertPrescription_空明细列表 - items为空时不调用batchInsert")
    void insertPrescription_空明细列表() {
        Prescription prescription = new Prescription();
        prescription.setMedicalRecordId(1);

        List<PrescriptionItem> items = new ArrayList<>();

        when(prescriptionDao.insert(any(Prescription.class))).thenReturn(1);

        int result = prescriptionService.insertPrescription(prescription, items);

        assertEquals(1, result);
        verify(prescriptionDao).insert(prescription);
        // 验证batchInsert未被调用
        verify(prescriptionItemDao, never()).batchInsert(anyList());
    }

    @Test
    @DisplayName("insertPrescription_null明细 - items为null时不调用batchInsert")
    void insertPrescription_null明细() {
        Prescription prescription = new Prescription();
        prescription.setMedicalRecordId(1);

        when(prescriptionDao.insert(any(Prescription.class))).thenReturn(1);

        int result = prescriptionService.insertPrescription(prescription, null);

        assertEquals(1, result);
        verify(prescriptionDao).insert(prescription);
        // 验证batchInsert未被调用
        verify(prescriptionItemDao, never()).batchInsert(anyList());
    }

    @Test
    @DisplayName("insertPrescription_明细项设置prescriptionId - 验证每个item的prescriptionId等于prescription.getId()")
    void insertPrescription_明细项设置prescriptionId() {
        Prescription prescription = new Prescription();
        prescription.setMedicalRecordId(1);

        PrescriptionItem item1 = new PrescriptionItem();
        item1.setDrugName("阿莫西林");

        PrescriptionItem item2 = new PrescriptionItem();
        item2.setDrugName("布洛芬");

        PrescriptionItem item3 = new PrescriptionItem();
        item3.setDrugName("头孢");

        List<PrescriptionItem> items = Arrays.asList(item1, item2, item3);

        // 模拟insert后设置id
        when(prescriptionDao.insert(any(Prescription.class))).thenAnswer(invocation -> {
            Prescription p = invocation.getArgument(0);
            p.setId(88);
            return 1;
        });
        when(prescriptionItemDao.batchInsert(anyList())).thenReturn(3);

        prescriptionService.insertPrescription(prescription, items);

        // 验证每个item的prescriptionId都等于prescription.getId()
        Integer expectedId = 88;
        assertEquals(expectedId, item1.getPrescriptionId());
        assertEquals(expectedId, item2.getPrescriptionId());
        assertEquals(expectedId, item3.getPrescriptionId());
    }

    // ==================== updatePrescriptionStatus 测试 ====================

    @Test
    @DisplayName("updatePrescriptionStatus_正常")
    void updatePrescriptionStatus_正常() {
        Integer id = 1;
        Integer status = 2;

        when(prescriptionDao.updateStatus(any(Prescription.class))).thenReturn(1);

        int result = prescriptionService.updatePrescriptionStatus(id, status);

        assertEquals(1, result);
        // 验证构造的Prescription对象属性正确
        verify(prescriptionDao).updateStatus(argThat(p ->
                p.getId().equals(id) && p.getStatus().equals(status)
        ));
    }

    // ==================== selectByMedicalRecordId 测试 ====================

    @Test
    @DisplayName("selectByMedicalRecordId_正常")
    void selectByMedicalRecordId_正常() {
        Integer medicalRecordId = 1;

        HashMap<String, Object> map1 = new HashMap<>();
        map1.put("id", 1);
        map1.put("type", 1);
        List<HashMap<String, Object>> list = new ArrayList<>();
        list.add(map1);

        when(prescriptionDao.selectByMedicalRecordId(medicalRecordId)).thenReturn(list);

        List<Map<String, Object>> result = prescriptionService.selectByMedicalRecordId(medicalRecordId);

        assertNotNull(result);
        assertEquals(1, result.size());
        verify(prescriptionDao).selectByMedicalRecordId(medicalRecordId);
    }

    @Test
    @DisplayName("selectByMedicalRecordId_无数据")
    void selectByMedicalRecordId_无数据() {
        Integer medicalRecordId = 999;

        when(prescriptionDao.selectByMedicalRecordId(medicalRecordId)).thenReturn(new ArrayList<>());

        List<Map<String, Object>> result = prescriptionService.selectByMedicalRecordId(medicalRecordId);

        assertNotNull(result);
        assertTrue(result.isEmpty());
        verify(prescriptionDao).selectByMedicalRecordId(medicalRecordId);
    }

    // ==================== selectItemsByPrescriptionId 测试 ====================

    @Test
    @DisplayName("selectItemsByPrescriptionId_正常")
    void selectItemsByPrescriptionId_正常() {
        Integer prescriptionId = 1;

        PrescriptionItem item1 = new PrescriptionItem();
        item1.setId(1);
        item1.setPrescriptionId(prescriptionId);
        item1.setDrugName("阿莫西林");

        List<PrescriptionItem> items = new ArrayList<>();
        items.add(item1);

        when(prescriptionItemDao.selectByPrescriptionId(prescriptionId)).thenReturn(items);

        List<PrescriptionItem> result = prescriptionService.selectItemsByPrescriptionId(prescriptionId);

        assertNotNull(result);
        assertEquals(1, result.size());
        assertEquals("阿莫西林", result.get(0).getDrugName());
        verify(prescriptionItemDao).selectByPrescriptionId(prescriptionId);
    }

    // ==================== selectByPatientId 测试 ====================

    @Test
    @DisplayName("selectByPatientId_正常 - 验证分页计算")
    void selectByPatientId_正常() {
        // 准备分页参数
        Map<String, Object> map = new HashMap<>();
        map.put("page", 2);
        map.put("length", 5);

        // mock 总数
        when(prescriptionDao.selectByPatientIdCount(map)).thenReturn(12L);

        // mock 列表数据
        HashMap<String, Object> prescription1 = new HashMap<>();
        prescription1.put("id", 6);
        List<HashMap<String, Object>> list = new ArrayList<>();
        list.add(prescription1);
        when(prescriptionDao.selectByPatientId(map)).thenReturn(list);

        // 执行
        PageUtils result = prescriptionService.selectByPatientId(map);

        // 验证PageUtils字段
        assertNotNull(result);
        assertEquals(12L, result.getTotalCount());
        assertEquals(2, result.getPageIndex());
        assertEquals(5, result.getPageSize());
        assertEquals(3, result.getTotalPage()); // 12/5=2.4，向上取整为3
        assertEquals(list, result.getList());

        // 验证分页计算: start = (page-1)*length = (2-1)*5 = 5
        assertEquals(5, map.get("start"));

        verify(prescriptionDao).selectByPatientIdCount(map);
        verify(prescriptionDao).selectByPatientId(map);
    }
}
