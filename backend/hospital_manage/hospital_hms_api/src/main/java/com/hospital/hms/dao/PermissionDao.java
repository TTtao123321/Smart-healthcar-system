package com.hospital.hms.dao;

import com.hospital.hms.pojo.Permission;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface PermissionDao {
    List<Permission> selectAllPermissions();
}
