package com.hospital.hms.config;

import com.hospital.hms.satoken.StpPatientUtil;
import org.springframework.context.annotation.Configuration;

import javax.annotation.PostConstruct;

/**
 * 患者端Sa-Token配置
 * 初始化患者端独立的StpLogic
 */
@Configuration
public class StpPatientConfig {

    @PostConstruct
    public void init() {
        // 注册患者端StpLogic到SaManager
        StpPatientUtil.init();
    }
}
