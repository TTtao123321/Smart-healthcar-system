package com.hospital.hms.dao;

import com.hospital.hms.pojo.MedicalDept;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public interface DeptDao {
    /**
     *
     * @param map
     * @return
     */
    Long selectConditionByPageCount(Map<String, Object> map);

    /**
     *
     * @param map
     * @return
     */
    List<HashMap<String, Object>> selectConditionByPage(Map<String, Object> map);

    /**
     *
     * @param map
     */
    void insert(MedicalDept map);

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
     * @return
     */
    long selectSubCountByIds(Integer[] ids);

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
     * @return
     */
    ArrayList<HashMap> selectDeptAndSub();
}
