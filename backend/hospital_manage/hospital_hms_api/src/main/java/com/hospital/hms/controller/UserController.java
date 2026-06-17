package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
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
            ArrayList roleNames = userService.selectUserRoleNames(userId);
            String tokenName = StpUtil.getTokenName();
            String token = StpUtil.getTokenValue();
            resultMap.put(CommonResult.RETURN_RESULT,"登录成功");
            resultMap.put("tokenName",tokenName);
            resultMap.put("token",token);
            resultMap.put("permissions",permissions);
            resultMap.put("roleNames",roleNames);
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

    @PostMapping("/selectUserByPage")
    @Operation(summary = "分页查询用户")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "USER:SELECT"}, mode = SaMode.OR)
    public CommonResult selectUserByPage(@RequestBody Map<String, Object> map) {
        try {
            int page = (int) map.getOrDefault("page", 1);
            int length = (int) map.getOrDefault("length", 10);
            map.put("start", (page - 1) * length);
            map.put("length", length);
            HashMap result = userService.selectUserByPage(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
        } catch (Exception e) {
            log.error("分页查询用户失败", e);
            return CommonResult.error("查询失败！");
        }
    }

    @GetMapping("/selectUserById")
    @Operation(summary = "根据ID查询用户")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "USER:SELECT"}, mode = SaMode.OR)
    public CommonResult selectUserById(@RequestParam Integer id) {
        try {
            HashMap result = userService.selectUserById(id);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
        } catch (Exception e) {
            log.error("查询用户失败, id:{}", id, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/insertUser")
    @Operation(summary = "添加用户")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "USER:INSERT"}, mode = SaMode.OR)
    public CommonResult insertUser(@RequestBody Map<String, Object> map) {
        try {
            map.put("root", 0);
            map.putIfAbsent("status", 1);
            int rows = userService.insertUser(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, rows);
        } catch (Exception e) {
            log.error("添加用户失败", e);
            return CommonResult.error("添加失败！");
        }
    }

    @PostMapping("/updateUser")
    @Operation(summary = "更新用户")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "USER:UPDATE"}, mode = SaMode.OR)
    public CommonResult updateUser(@RequestBody Map<String, Object> map) {
        try {
            int rows = userService.updateUser(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, rows);
        } catch (Exception e) {
            log.error("更新用户失败", e);
            return CommonResult.error("更新失败！");
        }
    }

    @PostMapping("/deleteUserByIds")
    @Operation(summary = "删除用户")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "USER:DELETE"}, mode = SaMode.OR)
    public CommonResult deleteUserByIds(@RequestBody Integer[] ids) {
        try {
            int rows = userService.deleteUserByIds(ids);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, rows);
        } catch (Exception e) {
            log.error("删除用户失败", e);
            return CommonResult.error("删除失败！");
        }
    }
}
