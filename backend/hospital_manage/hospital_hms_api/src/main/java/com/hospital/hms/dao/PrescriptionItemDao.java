package com.hospital.hms.dao;

import com.hospital.hms.pojo.PrescriptionItem;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PrescriptionItemDao {

    int batchInsert(List<PrescriptionItem> items);

    List<PrescriptionItem> selectByPrescriptionId(Integer prescriptionId);

    int deleteByPrescriptionId(Integer prescriptionId);
}
