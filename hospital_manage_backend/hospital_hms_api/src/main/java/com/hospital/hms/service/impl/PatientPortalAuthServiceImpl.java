package com.hospital.hms.service.impl;

import cn.hutool.core.util.RandomUtil;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.dao.PatientDao;
import com.hospital.hms.pojo.PatientUserInfo;
import com.hospital.hms.satoken.StpPatientUtil;
import com.hospital.hms.service.PatientPortalAuthService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * 患者端认证服务实现类
 */
@Slf4j
@Service
public class PatientPortalAuthServiceImpl implements PatientPortalAuthService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    @Autowired
    private PatientDao patientDao;

    /** 验证码Redis key前缀 */
    private static final String SMS_CODE_PREFIX = "sms:code:";
    /** 验证码有效期（分钟） */
    private static final long SMS_CODE_TTL_MINUTES = 5;

    @Override
    public CommonResult sendSmsCode(String phone) {
        // 生成6位随机验证码
        String code = RandomUtil.randomNumbers(6);
        String redisKey = SMS_CODE_PREFIX + phone;

        // 存入Redis，设置5分钟过期
        stringRedisTemplate.opsForValue().set(redisKey, code, SMS_CODE_TTL_MINUTES, TimeUnit.MINUTES);

        // 开发阶段：直接在日志和响应中返回验证码（生产环境对接短信服务商）
        log.info("【开发模式】手机号{}的验证码为：{}", phone, code);

        HashMap<String, Object> resultMap = new HashMap<>();
        resultMap.put("msg", "验证码已发送");
        // 开发阶段返回验证码，生产环境删除此行
        resultMap.put("code_dev", code);
        return CommonResult.ok(resultMap);
    }

    @Override
    public CommonResult login(String phone, String code) {
        String redisKey = SMS_CODE_PREFIX + phone;

        // 从Redis取出验证码
        String savedCode = stringRedisTemplate.opsForValue().get(redisKey);
        if (savedCode == null) {
            return CommonResult.error("验证码已过期，请重新获取");
        }
        if (!savedCode.equals(code)) {
            return CommonResult.error("验证码错误");
        }

        // 验证通过后删除验证码，防止重复使用
        stringRedisTemplate.delete(redisKey);

        // 查询患者信息（按手机号匹配）
        PatientUserInfo patient = patientDao.selectPatientByTel(phone);

        // 如果用户不存在，自动注册
        if (patient == null) {
            patient = new PatientUserInfo();
            patient.setUuid(UUID.randomUUID().toString().replace("-", ""));
            patient.setTel(phone);
            patient.setName("患者" + phone.substring(phone.length() - 4));
            patientDao.insertPatient(patient);
            log.info("自动注册患者，手机号：{}，患者ID：{}", phone, patient.getId());
        }

        // 使用患者端独立的StpLogic登录
        StpPatientUtil.login(patient.getId());
        String tokenValue = StpPatientUtil.getTokenValue();

        // 返回登录信息
        HashMap<String, Object> resultMap = new HashMap<>();
        resultMap.put("token", tokenValue);
        resultMap.put("patientId", patient.getId());
        resultMap.put("name", patient.getName());
        return CommonResult.ok(resultMap);
    }

    @Override
    public CommonResult logout() {
        StpPatientUtil.logout();
        return CommonResult.ok("登出成功");
    }
}
