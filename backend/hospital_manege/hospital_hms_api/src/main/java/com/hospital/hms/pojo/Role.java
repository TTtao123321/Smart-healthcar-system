package com.hospital.hms.pojo;

import lombok.Data;
import java.io.Serializable;

@Data
public class Role implements Serializable {
    private static final long serialVersionUID = 1L;
    private Integer id;
    private String roleName;
    private String permissions; // JSON string
    private String desc;
    private String defaultPermissions; // JSON string
    private Boolean systemic;
}
