package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.pojo.Permission;
import com.hospital.hms.service.PermissionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/permission")
@Tag(name = "PermissionController", description = "权限管理接口")
@Slf4j
public class PermissionController {
    @Autowired
    private PermissionService permissionService;

    @GetMapping("/selectAllPermissions")
    @Operation(summary = "查询所有权限")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "PERMISSION:SELECT"}, mode = SaMode.OR)
    public CommonResult selectAllPermissions() {
        try {
            List<Permission> result = permissionService.selectAllPermissions();
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
        } catch (Exception e) {
            log.error("查询所有权限失败", e);
            return CommonResult.error("查询失败！");
        }
    }
}
