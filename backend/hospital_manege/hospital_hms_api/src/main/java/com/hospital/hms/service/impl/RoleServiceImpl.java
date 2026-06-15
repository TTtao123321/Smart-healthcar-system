package com.hospital.hms.service.impl;

import com.hospital.hms.dao.RoleDao;
import com.hospital.hms.pojo.Role;
import com.hospital.hms.service.RoleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RoleServiceImpl implements RoleService {
    @Autowired
    private RoleDao roleDao;

    @Override
    public List<Role> selectAllRoles() {
        return roleDao.selectAllRoles();
    }

    @Override
    public Role selectRoleById(Integer id) {
        return roleDao.selectRoleById(id);
    }

    @Override
    public int insertRole(Role role) {
        return roleDao.insertRole(role);
    }

    @Override
    public int updateRole(Role role) {
        return roleDao.updateRole(role);
    }

    @Override
    public int deleteRoleById(Integer id) {
        return roleDao.deleteRoleById(id);
    }
}
