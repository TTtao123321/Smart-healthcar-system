# 诊费管理模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 HMS 后端开发 doctor_price 表的完整 CRUD API，对接现有前端页面。

**Architecture:** 遵循现有 Doctor 模块的分层模式（Pojo → Dao → Mapper XML → Service → Controller），新增 9 个文件，4 个 REST 接口。

**Tech Stack:** Spring Boot, MyBatis, Sa-Token, Swagger, Lombok, JSR-303 Validation

## Global Constraints

- 所有文件位于 `hospital_hms_api/src/main/java/com/hospital/hms/` 下
- 遵循现有代码风格：`@Slf4j`、`@Data`、`@Tag`、`@Operation`、`@SaCheckLogin`、`@SaCheckPermission`
- 返回统一 `CommonResult` 格式
- 权限命名：`MEDICAL:SELECT` / `MEDICAL:INSERT` / `MEDICAL:UPDATE` / `MEDICAL:DELETE`

---

### Task 1: DoctorPrice 实体类

**Files:**
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/pojo/DoctorPrice.java`

**Interfaces:**
- Produces: `DoctorPrice` class with fields: `id (Integer)`, `doctorId (Integer)`, `level (String)`, `price_1 (BigDecimal)`, `price_2 (BigDecimal)`
- 注：字段名用 `price_1`/`price_2` 而非 `price1`/`price2`，确保与前端 JSON key 和 BeanUtil.toBean 映射一致

- [ ] **Step 1: 创建 DoctorPrice.java**

```java
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
```

- [ ] **Step 2: 验证编译**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/hospital_manage_backend && mvn compile -pl hospital_hms_api -q 2>&1
```

Expected: BUILD SUCCESS

---

### Task 2: DoctorPriceDao 接口 + Mapper XML

**Files:**
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/dao/DoctorPriceDao.java`
- Create: `hospital_hms_api/src/main/resources/mapper/DoctorPriceDao.xml`

**Interfaces:**
- Consumes: `DoctorPrice` from Task 1
- Produces: `DoctorPriceDao` with methods:
  - `Long selectByPageCount(Map<String, Object> map)`
  - `List<HashMap<String, Object>> selectByPage(Map<String, Object> map)`
  - `void insert(DoctorPrice entity)`
  - `void update(Map<String, Object> param)`
  - `void deleteByIds(Integer[] ids)`

- [ ] **Step 1: 创建 DoctorPriceDao.java**

```java
package com.hospital.hms.dao;

import com.hospital.hms.pojo.DoctorPrice;
import org.springframework.stereotype.Repository;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public interface DoctorPriceDao {

    Long selectByPageCount(Map<String, Object> map);

    List<HashMap<String, Object>> selectByPage(Map<String, Object> map);

    void insert(DoctorPrice doctorPrice);

    void update(Map<String, Object> param);

    void deleteByIds(Integer[] ids);
}
```

- [ ] **Step 2: 创建 DoctorPriceDao.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper
        PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.hospital.hms.dao.DoctorPriceDao">

    <select id="selectByPageCount" parameterType="map" resultType="java.lang.Long">
        SELECT COUNT(dp.id)
        FROM doctor_price dp
        JOIN doctor d ON dp.doctor_id = d.id
        LEFT JOIN medical_dept_sub_doctor mdsd ON mdsd.doctor_id = d.id
        LEFT JOIN medical_dept_sub mds ON mdsd.dept_sub_id = mds.id
        LEFT JOIN medical_dept md ON mds.dept_id = md.id
        WHERE 1 = 1
        <if test="name != null">
            AND d.name LIKE CONCAT('%', #{name}, '%')
        </if>
        <if test="deptId != null">
            AND md.id = #{deptId}
        </if>
        <if test="job != null">
            AND d.job = #{job}
        </if>
        <if test="status != null">
            AND d.status = #{status}
        </if>
    </select>

    <select id="selectByPage" parameterType="map" resultType="java.util.HashMap">
        SELECT
            d.name AS doctorName,
            d.sex AS sex,
            d.job AS job,
            md.name AS deptName,
            mds.name AS deptSubName,
            dp.price_1 AS price_1,
            dp.price_2 AS price_2,
            dp.doctor_id AS doctorId,
            dp.id AS id,
            dp.level AS level
        FROM doctor_price dp
        JOIN doctor d ON dp.doctor_id = d.id
        LEFT JOIN medical_dept_sub_doctor mdsd ON mdsd.doctor_id = d.id
        LEFT JOIN medical_dept_sub mds ON mdsd.dept_sub_id = mds.id
        LEFT JOIN medical_dept md ON mds.dept_id = md.id
        WHERE 1 = 1
        <if test="name != null">
            AND d.name LIKE CONCAT('%', #{name}, '%')
        </if>
        <if test="deptId != null">
            AND md.id = #{deptId}
        </if>
        <if test="job != null">
            AND d.job = #{job}
        </if>
        <if test="status != null">
            AND d.status = #{status}
        </if>
        <if test="order != null">
            ORDER BY md.id ${order}
        </if>
        LIMIT #{length} OFFSET #{start}
    </select>

    <insert id="insert" parameterType="com.hospital.hms.pojo.DoctorPrice">
        INSERT INTO doctor_price (doctor_id, level, price_1, price_2)
        VALUES (#{doctorId}, #{level}, #{price_1}, #{price_2})
    </insert>

    <update id="update" parameterType="map">
        UPDATE doctor_price
        SET price_1 = #{price_1},
            price_2 = #{price_2},
            level = #{level}
        WHERE id = #{id}
    </update>

    <delete id="deleteByIds">
        DELETE FROM doctor_price
        WHERE id IN
        <foreach collection="array" open="(" item="one" separator="," close=")">
            #{one}
        </foreach>
    </delete>

</mapper>
```

- [ ] **Step 3: 验证编译**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/hospital_manage_backend && mvn compile -pl hospital_hms_api -q 2>&1
```

Expected: BUILD SUCCESS

---

### Task 3: DoctorPriceService 接口 + 实现

**Files:**
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/service/DoctorPriceService.java`
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/service/impl/DoctorPriceServiceImpl.java`

**Interfaces:**
- Consumes: `DoctorPriceDao` from Task 2, `PageUtils` from common
- Produces: `DoctorPriceService` with methods:
  - `PageUtils selectByPage(Map<String, Object> map)`
  - `void insert(Map<String, Object> map)`
  - `void update(Map<String, Object> param)`
  - `void deleteByIds(Integer[] ids)`

- [ ] **Step 1: 创建 DoctorPriceService.java**

```java
package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public interface DoctorPriceService {

    PageUtils selectByPage(Map<String, Object> map);

    void insert(Map<String, Object> map);

    void update(Map<String, Object> param);

    void deleteByIds(Integer[] ids);
}
```

- [ ] **Step 2: 创建 DoctorPriceServiceImpl.java**

```java
package com.hospital.hms.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.map.MapUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.DoctorPriceDao;
import com.hospital.hms.pojo.DoctorPrice;
import com.hospital.hms.service.DoctorPriceService;
import lombok.extern.log4j.Log4j2;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Log4j2
@Service
public class DoctorPriceServiceImpl implements DoctorPriceService {

    @Autowired
    private DoctorPriceDao doctorPriceDao;

    @Override
    public PageUtils selectByPage(Map<String, Object> map) {
        int page = MapUtil.getInt(map, "page", 1);
        int length = MapUtil.getInt(map, "length", 10);
        Long totalCount = doctorPriceDao.selectByPageCount(map);
        if (totalCount == 0) {
            return new PageUtils(Collections.emptyList(), totalCount, page, length);
        }
        int startId = (page - 1) * length;
        map.put("start", startId);
        List<HashMap<String, Object>> list = doctorPriceDao.selectByPage(map);
        return new PageUtils(list, totalCount, page, length);
    }

    @Override
    @Transactional
    public void insert(Map<String, Object> map) {
        DoctorPrice doctorPrice = BeanUtil.toBean(map, DoctorPrice.class);
        doctorPriceDao.insert(doctorPrice);
    }

    @Override
    @Transactional
    public void update(Map<String, Object> param) {
        doctorPriceDao.update(param);
    }

    @Override
    @Transactional
    public void deleteByIds(Integer[] ids) {
        doctorPriceDao.deleteByIds(ids);
    }
}
```

- [ ] **Step 3: 验证编译**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/hospital_manage_backend && mvn compile -pl hospital_hms_api -q 2>&1
```

Expected: BUILD SUCCESS

---

### Task 4: Form 表单类（4 个）

**Files:**
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectDoctorPriceByPageForm.java`
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/controller/form/InsertDoctorPriceForm.java`
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/controller/form/UpdateDoctorPriceForm.java`
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/controller/form/DeleteDoctorPriceByIdsForm.java`

**Interfaces:**
- Produces: 4 Form classes with JSR-303 validation

- [ ] **Step 1: 创建 SelectDoctorPriceByPageForm.java**

```java
package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import org.hibernate.validator.constraints.Range;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;

@Data
@Schema(description = "查询诊费分页表单")
public class SelectDoctorPriceByPageForm {

    @Pattern(regexp = "^[\\u4e00-\\u9fa5]{1,20}$", message = "name内容不正确")
    private String name;

    @Min(value = 1, message = "deptId不能小于1")
    private Integer deptId;

    @Pattern(regexp = "^主治医师$|^副主治医师$|^主任医师$|^副主任医师$", message = "job内容不正确")
    private String job;

    @Range(min = 1, max = 3, message = "status内容不正确")
    private Byte status;

    @Pattern(regexp = "^ASC$|^DESC$", message = "order内容不正确")
    private String order;

    @NotNull(message = "page不能为空")
    @Min(value = 1, message = "page不能小于1")
    private Integer page;

    @NotNull(message = "length不能为空")
    @Range(min = 10, max = 50, message = "length内容不正确")
    private Integer length;
}
```

- [ ] **Step 2: 创建 InsertDoctorPriceForm.java**

```java
package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;

@Schema(description = "新增诊费表单")
@Data
public class InsertDoctorPriceForm {

    @NotNull(message = "doctorId不能为空")
    @Min(value = 1, message = "doctorId不能小于1")
    @Schema(description = "医生ID")
    private Integer doctorId;

    @NotBlank(message = "level不能为空")
    @Pattern(regexp = "^主治医师$|^副主治医师$|^主任医师$|^副主任医师$", message = "level内容不正确")
    @Schema(description = "职称级别")
    private String level;

    @NotNull(message = "price_1不能为空")
    @Schema(description = "门诊挂号费")
    private java.math.BigDecimal price_1;

    @NotNull(message = "price_2不能为空")
    @Schema(description = "视频问诊挂号费")
    private java.math.BigDecimal price_2;
}
```

- [ ] **Step 3: 创建 UpdateDoctorPriceForm.java**

```java
package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;

@Schema(description = "更新诊费表单")
@Data
public class UpdateDoctorPriceForm {

    @NotNull(message = "id不能为空")
    @Min(value = 1, message = "id不能小于1")
    @Schema(description = "诊费ID")
    private Integer id;

    @NotBlank(message = "level不能为空")
    @Pattern(regexp = "^主治医师$|^副主治医师$|^主任医师$|^副主任医师$", message = "level内容不正确")
    @Schema(description = "职称级别")
    private String level;

    @NotNull(message = "price_1不能为空")
    @Schema(description = "门诊挂号费")
    private java.math.BigDecimal price_1;

    @NotNull(message = "price_2不能为空")
    @Schema(description = "视频问诊挂号费")
    private java.math.BigDecimal price_2;
}
```

- [ ] **Step 4: 创建 DeleteDoctorPriceByIdsForm.java**

```java
package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;

@Schema(description = "删除诊费表单")
@Data
public class DeleteDoctorPriceByIdsForm {

    @NotEmpty(message = "ids不能为空")
    @Schema(description = "诊费ID")
    private Integer[] ids;
}
```

- [ ] **Step 5: 验证编译**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/hospital_manage_backend && mvn compile -pl hospital_hms_api -q 2>&1
```

Expected: BUILD SUCCESS

---

### Task 5: DoctorPriceController

**Files:**
- Create: `hospital_hms_api/src/main/java/com/hospital/hms/controller/DoctorPriceController.java`

**Interfaces:**
- Consumes: `DoctorPriceService` from Task 3, Form classes from Task 4
- Produces: REST endpoints at `/doctor_price`

- [ ] **Step 1: 创建 DoctorPriceController.java**

```java
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
```

- [ ] **Step 2: 验证编译**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/hospital_manage_backend && mvn compile -pl hospital_hms_api -q 2>&1
```

Expected: BUILD SUCCESS

---

### Task 6: 集成验证

**Files:**
- No new files. Verify all files compile and the API is reachable.

- [ ] **Step 1: 完整编译**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/hospital_manage_backend && mvn compile -pl hospital_hms_api -q 2>&1
```

Expected: BUILD SUCCESS

- [ ] **Step 2: 启动服务并测试 API**

```bash
# 启动服务（如已运行则跳过）
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/hospital_manage_backend && mvn spring-boot:run -pl hospital_hms_api &

# 测试分页查询接口
curl -s -X POST http://localhost:8080/doctor_price/selectByPage \
  -H "Content-Type: application/json" \
  -d '{"page":1,"length":10}' 2>&1 | head -c 500
```

Expected: 返回 JSON，包含 `code: 200` 和分页数据

- [ ] **Step 3: 验证数据库数据可查询**

确认返回的 `result.list` 中包含之前初始化的 17 条诊费记录，每行包含 `doctorName, sex, job, deptName, deptSubName, price_1, price_2, doctorId`。