package com.hospital.hms.dao;

import com.hospital.hms.pojo.MedicalRegistration;
import org.apache.ibatis.annotations.Mapper;
import org.springframework.stereotype.Repository;

import java.util.HashMap;

@Mapper
@Repository
public interface MedicalRegistrationDao {
    int insert(MedicalRegistration entity);

    HashMap<String, Object> selectScheduleById(Integer doctorScheduleId);

    int increaseScheduleNum(Integer doctorScheduleId);
}
