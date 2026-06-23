package com.hospital.hms.pojo;

import lombok.Data;

import java.io.Serializable;

@Data
public class PrescriptionItem implements Serializable {

    private static final long serialVersionUID = 1L;

    private Integer id;
    private Integer prescriptionId;
    private String drugName;
    private String specification;
    private Integer quantity;
    private String dosage;
    private String frequency;
    private Integer days;
    private String remark;
}
