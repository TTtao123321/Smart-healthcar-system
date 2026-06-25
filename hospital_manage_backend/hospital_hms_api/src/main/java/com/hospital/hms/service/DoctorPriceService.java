package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;

import java.util.Map;

public interface DoctorPriceService {

    PageUtils selectByPage(Map<String, Object> map);

    void insert(Map<String, Object> map);

    void update(Map<String, Object> param);

    void deleteByIds(Integer[] ids);
}
