package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.stp.StpUtil;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.LoginForm;
import com.hospital.hms.controller.form.UpdateUserPasswordForm;
import com.hospital.hms.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/user")
@Tag(name = "UserController",description = "用户管理接口")
@Slf4j
public class UserController {
    @Autowired
    private UserService userService;

    @PostMapping("/login")
    @Operation(summary = "用户登录")
    public CommonResult login(@RequestBody @Valid LoginForm form){
        Map<String, Object> map = BeanUtil.beanToMap(form);
        Integer userId = userService.login(map);
        if(userId != null){
            HashMap<String, Object> resultMap = new HashMap<>();
            StpUtil.login(userId);
            ArrayList permissions = userService.selectUserPermssions(userId);
            String tokenName = StpUtil.getTokenName();
            String token = StpUtil.getTokenValue();
            resultMap.put(CommonResult.RETURN_RESULT,"登录成功");
            resultMap.put("tokenName",tokenName);
            resultMap.put("token",token);
            resultMap.put("permissions",permissions);
            log.info("User logged in: userId={}, token={}, tokenName={}", userId, token, tokenName);
            return CommonResult.ok(resultMap);
        }else {
            return CommonResult.ok().put(CommonResult.RETURN_RESULT,"登录失败");
        }
    }

    @GetMapping("/logout")
    @SaCheckLogin
    @Operation(summary = "退出登录")
    public CommonResult logout() {
        StpUtil.logout();
        return CommonResult.ok();
    }

    @PostMapping("/updatePassword")
    @SaCheckLogin
    @Operation(summary = "修改密码")
    public CommonResult updatePassword(@Valid @RequestBody UpdateUserPasswordForm param){
        Map<String, Object> map = BeanUtil.beanToMap(param);
        Integer userId = StpUtil.getLoginIdAsInt();
        map.put("userId",userId);
        Integer rows = userService.updatePassword(map);
        return CommonResult.ok().put(CommonResult.RETURN_RESULT,rows);
    }
}
