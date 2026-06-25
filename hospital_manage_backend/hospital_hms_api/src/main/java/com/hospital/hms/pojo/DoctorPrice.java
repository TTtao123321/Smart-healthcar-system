package com.hospital.hms.pojo;

import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;

@Data
public class DoctorPrice implements Serializable {

    private static final long serialVersionUID = 1L;

    private Integer id;
    private Integer doctorId;
    private String level;
    private BigDecimal price_1;
    private BigDecimal price_2;
}
