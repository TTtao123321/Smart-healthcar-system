package com.hospital.hms.dao;

import com.hospital.hms.pojo.Role;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface RoleDao {
    List<Role> selectAllRoles();
    Role selectRoleById(Integer id);
    int insertRole(Role role);
    int updateRole(Role role);
    int deleteRoleById(Integer id);
    List<String> selectRoleNamesByUserId(Integer userId);
}
