package com.hospital.hms.dao;

import com.hospital.hms.pojo.DoctorPrice;
import org.springframework.stereotype.Repository;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public interface DoctorPriceDao {

    Long selectByPageCount(Map<String, Object> map);

    List<HashMap<String, Object>> selectByPage(Map<String, Object> map);

    void insert(DoctorPrice doctorPrice);

    void update(Map<String, Object> param);

    void deleteByIds(Integer[] ids);
}
