package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.pojo.MedicalDeptSub;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;

@Service
public interface DeptSubService {
    /**
     *
     * @param map
     * @return
     */
    PageUtils selectConditionByPage(HashMap map);

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
     */
    void deleteByIds(Integer[] ids);

    ArrayList<HashMap> selectSubByDeptId(Integer deptId);
}
