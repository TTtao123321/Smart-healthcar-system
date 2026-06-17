package com.hospital.hms.pojo;

import lombok.Data;

import java.io.Serializable;
import java.util.Date;

@Data
public class MedicalRecord implements Serializable {

    private static final long serialVersionUID = 1L;

    private Integer id;
    private String uuid;
    private Integer registrationId;
    private Integer patientId;
    private Integer doctorId;
    private Integer deptSubId;
    private String chiefComplaint;
    private String presentIllness;
    private String physicalExam;
    private String diagnosis;
    private String doctorAdvice;
    private String remark;
    private Date createTime;
    private Date updateTime;
}
