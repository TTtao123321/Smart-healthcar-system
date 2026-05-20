package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Service
public interface DoctorService {
    /**
     *
     * @param map
     * @return
     */
    PageUtils selectConditionByPage(Map<String, Object> map);

    /**
     *
     * @param map
     */
    void insert(Map<String, Object> map);

    /**
     *
     * @param id
     * @return
     */
    HashMap selectById(Integer id);

    /**
     *
     * @param param
     */
    void update(Map<String, Object> param);

    /**
     *
     * @param ids
     */
    void deleteDoctorByIds(Integer[] ids);

    /**
     *
     * @param id
     * @return
     */
    HashMap selectDoctorDetailById(Integer id);

    /**
     *
     * @param file
     * @param doctorId
     */
    void updatePhoto(MultipartFile file, Integer doctorId);

    /**
     *
     * @param deptSubId
     * @return
     */
    ArrayList<HashMap> selectDoctorsBySubId(Integer deptSubId);

}
