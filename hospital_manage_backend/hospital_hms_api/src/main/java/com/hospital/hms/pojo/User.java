package com.hospital.hms.pojo;

import lombok.Data;
import java.io.Serializable;
import java.util.Date;

@Data
public class User implements Serializable {
    private static final long serialVersionUID = 1L;
    private Integer id;
    private String username;
    private String password;
    private String name;
    private String sex;
    private String tel;
    private String email;
    private String job;
    private String role; // JSON string
    private Boolean root;
    private Integer deptId;
    private Integer status;
    private Date createTime;
    private Integer doctorId;
    private Date hiredate;
    private String deptName; // from join
}
