package com.hospital.hms.service;

import com.hospital.hms.pojo.Role;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public interface RoleService {
    List<Role> selectAllRoles();
    Role selectRoleById(Integer id);
    int insertRole(Role role);
    int updateRole(Role role);
    int deleteRoleById(Integer id);
}
