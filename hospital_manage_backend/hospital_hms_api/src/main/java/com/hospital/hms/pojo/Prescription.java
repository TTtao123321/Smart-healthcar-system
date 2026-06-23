package com.hospital.hms.pojo;

import lombok.Data;

import java.io.Serializable;
import java.util.Date;

@Data
public class Prescription implements Serializable {

    private static final long serialVersionUID = 1L;

    private Integer id;
    private String uuid;
    private Integer medicalRecordId;
    private Integer patientId;
    private Integer doctorId;
    private Integer type;
    private Integer status;
    private Date createTime;
    private Date updateTime;
}
