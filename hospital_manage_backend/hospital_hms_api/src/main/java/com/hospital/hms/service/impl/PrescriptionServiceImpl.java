package com.hospital.hms.service.impl;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.PrescriptionDao;
import com.hospital.hms.dao.PrescriptionItemDao;
import com.hospital.hms.pojo.Prescription;
import com.hospital.hms.pojo.PrescriptionItem;
import com.hospital.hms.service.PrescriptionService;
import cn.hutool.core.map.MapUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class PrescriptionServiceImpl implements PrescriptionService {

    @Autowired
    private PrescriptionDao prescriptionDao;

    @Autowired
    private PrescriptionItemDao prescriptionItemDao;

    @Override
    @Transactional
    public int insertPrescription(Prescription prescription, List<PrescriptionItem> items) {
        int rows = prescriptionDao.insert(prescription);
        if (items != null && !items.isEmpty()) {
            for (PrescriptionItem item : items) {
                item.setPrescriptionId(prescription.getId());
            }
            prescriptionItemDao.batchInsert(items);
        }
        return rows;
    }

    @Override
    public int updatePrescriptionStatus(Integer id, Integer status) {
        Prescription prescription = new Prescription();
        prescription.setId(id);
        prescription.setStatus(status);
        return prescriptionDao.updateStatus(prescription);
    }

    @Override
    public Prescription selectById(Integer id) {
        return prescriptionDao.selectById(id);
    }

    @Override
    public List<Map<String, Object>> selectByMedicalRecordId(Integer medicalRecordId) {
        List<HashMap<String, Object>> list = prescriptionDao.selectByMedicalRecordId(medicalRecordId);
        return (List<Map<String, Object>>) (List<?>) list;
    }

    @Override
    public PageUtils selectByPatientId(Map<String, Object> map) {
        Long totalCount = prescriptionDao.selectByPatientIdCount(map);
        int page = MapUtil.getInt(map, "page");
        int length = MapUtil.getInt(map, "length");
        int start = (page - 1) * length;
        map.put("start", start);
        List<HashMap<String, Object>> list = prescriptionDao.selectByPatientId(map);
        return new PageUtils(list, totalCount, page, length);
    }

    @Override
    public List<PrescriptionItem> selectItemsByPrescriptionId(Integer prescriptionId) {
        return prescriptionItemDao.selectByPrescriptionId(prescriptionId);
    }

    @Override
    @Transactional
    public int deletePrescriptionById(Integer id) {
        prescriptionDao.deleteItemsByPrescriptionId(id);
        return prescriptionDao.deleteById(id);
    }
}
