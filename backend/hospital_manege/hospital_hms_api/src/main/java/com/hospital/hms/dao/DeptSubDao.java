package com.hospital.hms.dao;

import com.hospital.hms.pojo.MedicalDeptSub;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

@Repository
public interface DeptSubDao {
    /**
     *
     * @param map
     * @return
     */
    Long selectConditionByPageCount(HashMap map);

    /**
     *
     * @param map
     * @return
     */
    List<HashMap<String, Object>> selectConditionByPage(HashMap map);

    /**
     *
     * @param deptSub
     */
    void insert(MedicalDeptSub deptSub);

    /**
     *
     * @param id
     * @return
     */
    HashMap selectById(Integer id);

    /**
     *
     * @param deptSub
     */
    void update(MedicalDeptSub deptSub);

    /**
     *
     * @param ids
     * @return
     */
    long selectDoctorCountByIds(Integer[] ids);

    /**
     *
     * @param ids
     */
    void deleteByIds(Integer[] ids);

    ArrayList<HashMap> selectSubByDeptId(Integer deptId);
}
