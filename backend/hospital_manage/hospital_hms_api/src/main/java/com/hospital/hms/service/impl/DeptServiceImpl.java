package com.hospital.hms.service.impl;

import cn.hutool.core.map.MapUtil;
import com.hospital.common.exception.GlobalException;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.OperationMessage;
import com.hospital.hms.dao.DeptDao;
import com.hospital.hms.pojo.MedicalDept;
import com.hospital.hms.service.DeptService;
import lombok.extern.log4j.Log4j2;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Log4j2
@Service
public class DeptServiceImpl implements DeptService {
    @Autowired
    private DeptDao deptDao;

    @Override
    public PageUtils selectConditionByPage(Map<String, Object> map) {
        Long totalCount = deptDao.selectConditionByPageCount(map);
        if (totalCount == 0) {
            return new PageUtils(Collections.emptyList(), totalCount,
                    MapUtil.getInt(map, "page"),
                    MapUtil.getInt(map, "length"));
        }
        Long pageIndex = MapUtil.getLong(map,"page");
        Long pageSize = MapUtil.getLong(map,"length");
        Long startId = (pageIndex - 1) * pageSize;
        map.put("start",startId);
        List<HashMap<String,Object>> list = deptDao.selectConditionByPage(map);
        return new PageUtils(list,totalCount,MapUtil.getInt(map, "page"), MapUtil.getInt(map, "length"));
    }

    @Override
    @Transactional
    public void insert(MedicalDept dept) {
        deptDao.insert(dept);
    }

    @Override
    public HashMap selectById(Integer id) {
        return deptDao.selectById(id);
    }

    @Override
    @Transactional
    public void update(MedicalDept dept) {
        deptDao.update(dept);
    }

    @Override
    @Transactional
    public void deleteByIds(Integer[] ids) {
        long count = deptDao.selectSubCountByIds(ids);
        if (count == 0) {
            deptDao.deleteByIds(ids);
        }else {
            log.error("科室下有关联诊室，不可删除！");
            throw new GlobalException(OperationMessage.DEPTSUB_EXISTS.toString());
        }
    }

    @Override
    public ArrayList<HashMap> selectAllDeptNameAndId() {
        return deptDao.selectAllDeptNameAndId();
    }

    @Override
    public HashMap selectDeptAndSub() {
        ArrayList<HashMap> list = deptDao.selectDeptAndSub();
        LinkedHashMap<String,ArrayList> map = new LinkedHashMap();
        for (HashMap<String, Object> instance : list) {
            String deptName = (String) instance.get("deptName"); // 获取科室名称
            Integer subId = (Integer) instance.get("subId"); // 获取子部门ID
            String subName = (String) instance.get("subName"); // 获取子诊室名称
            map.computeIfAbsent(deptName, k -> new ArrayList<>()).add(new HashMap<>() {{
                        put("subId", subId);
                        put("subName", subName);
                    }});
        }
        return map;
    }
}
