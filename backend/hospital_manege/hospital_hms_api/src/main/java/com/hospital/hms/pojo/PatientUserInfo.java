package com.hospital.hms.pojo;

import lombok.Data;

import java.io.Serializable;
import java.util.Date;

@Data
public class PatientUserInfo implements Serializable {

    private static final long serialVersionUID = 1L;

    private Integer id;
    private String uuid;
    private String name;
    private String sex;
    private String pid;
    private String tel;
    private Date birthday;
    private String password;
    private String medicalHistory;
}
