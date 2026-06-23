package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.pojo.Role;
import com.hospital.hms.service.RoleService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/role")
@Tag(name = "RoleController", description = "角色管理接口")
@Slf4j
public class RoleController {
    @Autowired
    private RoleService roleService;

    @GetMapping("/selectAllRoles")
    @Operation(summary = "查询所有角色")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "ROLE:SELECT"}, mode = SaMode.OR)
    public CommonResult selectAllRoles() {
        try {
            List<Role> result = roleService.selectAllRoles();
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
        } catch (Exception e) {
            log.error("查询所有角色失败", e);
            return CommonResult.error("查询失败！");
        }
    }

    @GetMapping("/selectRoleById")
    @Operation(summary = "根据ID查询角色")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "ROLE:SELECT"}, mode = SaMode.OR)
    public CommonResult selectRoleById(@RequestParam Integer id) {
        try {
            Role result = roleService.selectRoleById(id);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
        } catch (Exception e) {
            log.error("查询角色失败, id:{}", id, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/insertRole")
    @Operation(summary = "添加角色")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "ROLE:INSERT"}, mode = SaMode.OR)
    public CommonResult insertRole(@RequestBody Role role) {
        try {
            role.setSystemic(false);
            int rows = roleService.insertRole(role);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, rows);
        } catch (Exception e) {
            log.error("添加角色失败, role:{}", role, e);
            return CommonResult.error("添加失败！");
        }
    }

    @PostMapping("/updateRole")
    @Operation(summary = "更新角色")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "ROLE:UPDATE"}, mode = SaMode.OR)
    public CommonResult updateRole(@RequestBody Role role) {
        try {
            int rows = roleService.updateRole(role);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, rows);
        } catch (Exception e) {
            log.error("更新角色失败, role:{}", role, e);
            return CommonResult.error("更新失败！");
        }
    }

    @PostMapping("/deleteRoleById")
    @Operation(summary = "删除角色")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "ROLE:DELETE"}, mode = SaMode.OR)
    public CommonResult deleteRoleById(@RequestParam Integer id) {
        try {
            int rows = roleService.deleteRoleById(id);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, rows);
        } catch (Exception e) {
            log.error("删除角色失败, id:{}", id, e);
            return CommonResult.error("删除失败！");
        }
    }
}
