package com.hospital.hms.config;

import cn.dev33.satoken.stp.StpInterface;
import com.hospital.hms.dao.RoleDao;
import com.hospital.hms.dao.UserDao;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

@Component
public class StpInterfaceConfig implements StpInterface {
    @Autowired
    private UserDao userDao;

    @Autowired
    private RoleDao roleDao;

    /**
     * 返回一个用户所拥有的权限集合
     */
    @Override
    public List<String> getPermissionList(Object loginId, String loginKey) {
        int userId = Integer.parseInt(loginId.toString());
        Set<String> permissions = userDao.selectUserPrivileges(userId);
        ArrayList list = new ArrayList();
        list.addAll(permissions);
        return list;
    }

    /**
     * 返回一个用户所拥有的角色集合
     */
    @Override
    public List<String> getRoleList(Object loginId, String loginKey) {
        int userId = Integer.parseInt(loginId.toString());
        List<String> roleNames = roleDao.selectRoleNamesByUserId(userId);
        return roleNames;
    }
}