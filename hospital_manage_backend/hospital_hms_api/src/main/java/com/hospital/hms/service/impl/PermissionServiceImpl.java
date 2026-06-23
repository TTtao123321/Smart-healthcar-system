package com.hospital.hms.service.impl;

import com.hospital.hms.dao.PermissionDao;
import com.hospital.hms.pojo.Permission;
import com.hospital.hms.service.PermissionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class PermissionServiceImpl implements PermissionService {
    @Autowired
    private PermissionDao permissionDao;

    @Override
    public List<Permission> selectAllPermissions() {
        return permissionDao.selectAllPermissions();
    }
}
