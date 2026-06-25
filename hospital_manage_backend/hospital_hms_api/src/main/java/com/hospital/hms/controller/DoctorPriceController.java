package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.DeleteDoctorPriceByIdsForm;
import com.hospital.hms.controller.form.InsertDoctorPriceForm;
import com.hospital.hms.controller.form.SelectDoctorPriceByPageForm;
import com.hospital.hms.controller.form.UpdateDoctorPriceForm;
import com.hospital.hms.service.DoctorPriceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.util.Map;

@RestController
@RequestMapping("/doctor_price")
@Tag(name = "DoctorPriceController", description = "诊费管理")
@Slf4j
public class DoctorPriceController {

    @Autowired
    private DoctorPriceService doctorPriceService;

    @PostMapping("/selectByPage")
    @Operation(summary = "分页查询诊费")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectByPage(@RequestBody @Valid SelectDoctorPriceByPageForm form) {
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            PageUtils result = doctorPriceService.selectByPage(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
        } catch (Exception e) {
            log.error("查询诊费失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/insert")
    @Operation(summary = "新增诊费")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:INSERT"}, mode = SaMode.OR)
    public CommonResult insert(@RequestBody @Valid InsertDoctorPriceForm form) {
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            doctorPriceService.insert(map);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("新增诊费失败, form:{}", form, e);
            return CommonResult.error("新增失败！");
        }
    }

    @PostMapping("/update")
    @Operation(summary = "更新诊费")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:UPDATE"}, mode = SaMode.OR)
    public CommonResult update(@RequestBody @Valid UpdateDoctorPriceForm form) {
        try {
            Map<String, Object> param = BeanUtil.beanToMap(form);
            doctorPriceService.update(param);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("更新诊费失败, form:{}", form, e);
            return CommonResult.error("更新失败！");
        }
    }

    @PostMapping("/deleteByIds")
    @Operation(summary = "批量删除诊费")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:DELETE"}, mode = SaMode.OR)
    public CommonResult deleteByIds(@RequestBody @Valid DeleteDoctorPriceByIdsForm form) {
        try {
            Integer[] ids = form.getIds();
            doctorPriceService.deleteByIds(ids);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("删除诊费失败, form:{}", form, e);
            return CommonResult.error("删除失败！");
        }
    }
}
