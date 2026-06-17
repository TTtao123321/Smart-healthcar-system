package com.hospital.hms.service;

import com.hospital.hms.common.CommonResult;

import java.util.Map;

/**
 * 患者端认证服务接口
 */
public interface PatientPortalAuthService {

    /**
     * 发送短信验证码
     * @param phone 手机号
     * @return 操作结果
     */
    CommonResult sendSmsCode(String phone);

    /**
     * 患者端登录（验证码登录，自动注册）
     * @param phone 手机号
     * @param code 验证码
     * @return 登录结果（包含token、patientId、name）
     */
    CommonResult login(String phone, String code);

    /**
     * 患者端登出
     * @return 操作结果
     */
    CommonResult logout();
}
