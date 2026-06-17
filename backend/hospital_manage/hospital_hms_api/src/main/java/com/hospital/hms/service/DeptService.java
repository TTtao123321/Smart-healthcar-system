package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.pojo.MedicalDept;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Service
public interface DeptService {
    /**
     *
     * @param map
     * @return
     */
    PageUtils selectConditionByPage(Map<String, Object> map);

    /**
     *
     * @param dept
     * @return
     */
    void insert(MedicalDept dept);

    /**
     *
     * @param id
     * @return
     */
    HashMap selectById(Integer id);

    /**
     *
     * @param dept
     */
    void update(MedicalDept dept);

    /**
     *
     * @param ids
     */
    void deleteByIds(Integer[] ids);

    /**
     *
     * @return
     */
    ArrayList<HashMap> selectAllDeptNameAndId();

    /**
     *
     * @return
     */
    HashMap selectDeptAndSub();
}
