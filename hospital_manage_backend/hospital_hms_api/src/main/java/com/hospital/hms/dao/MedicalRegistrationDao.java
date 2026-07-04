package com.hospital.hms.dao;

import com.hospital.hms.pojo.MedicalRegistration;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.HashMap;

@Mapper
@Repository
public interface MedicalRegistrationDao {
    int insert(MedicalRegistration entity);

    HashMap<String, Object> selectScheduleById(Integer doctorScheduleId);

    HashMap<String, Object> selectScheduleForUpdate(Integer doctorScheduleId);

    int increaseScheduleNum(Integer doctorScheduleId);

    HashMap<String, Object> selectRegistrationById(Integer registrationId);

    int updateRegistrationStatus(@Param("registrationId") Integer registrationId, @Param("status") Integer status);

    int decreaseScheduleNum(Integer doctorScheduleId);
}
