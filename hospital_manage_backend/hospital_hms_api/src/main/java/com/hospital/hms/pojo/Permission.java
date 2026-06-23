package com.hospital.hms.pojo;

import lombok.Data;
import java.io.Serializable;

@Data
public class Permission implements Serializable {
    private static final long serialVersionUID = 1L;
    private Integer id;
    private String permissionName;
    private Integer moduleId;
    private Integer actionId;
    private String moduleName; // from join
    private String actionName; // from join
}
