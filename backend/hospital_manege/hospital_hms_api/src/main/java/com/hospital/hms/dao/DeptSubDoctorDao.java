package com.hospital.hms.dao;

import com.hospital.hms.pojo.MedicalDeptSubDoctor;
import org.springframework.stereotype.Repository;

import java.util.Map;

@Repository
public interface DeptSubDoctorDao {
    /**
     *
     * @param medicalDeptSubDoctor
     */
    void insert(MedicalDeptSubDoctor medicalDeptSubDoctor);

    /**
     *
     * @param map
     */
    void update(Map<String, Object> map);

    /**
     *
     * @param ids
     */
    void deleteByIds(Integer[] ids);
}
