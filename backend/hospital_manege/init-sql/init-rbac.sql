/*
 RBAC 权限体系重构脚本

 数据库: MySQL 5.7
 Schema: fm_hospital
 日期: 2026-06-15

 说明:
   1. 重构 module 表，适配医院管理系统业务模块
   2. action 表保持不变
   3. 重构 permission 表，基于新模块重新定义权限
   4. 重构 role 表，定义超级管理员、医生、运营三种角色
   5. 更新 users 表的 role 字段，映射到新角色体系
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. 清空并重建 module 表（模块资源表）
-- ============================================================
TRUNCATE TABLE `module`;

INSERT INTO `module` (`id`, `module_code`, `module_name`) VALUES
(1, 'ORG',      '组织管理'),
(2, 'MEDICAL',  '医护管理'),
(3, 'SCHEDULE', '出诊管理'),
(4, 'SYSTEM',   '系统管理');

-- ============================================================
-- 2. action 表保持不变（INSERT/DELETE/UPDATE/SELECT/APPROVAL/EXPORT/BACKUP/ARCHIVE）
--    无需操作
-- ============================================================

-- ============================================================
-- 3. 清空并重建 permission 表（权限表）
--    permission_name 为唯一键，module_id+action_id 可重复
-- ============================================================
TRUNCATE TABLE `permission`;

INSERT INTO `permission` (`id`, `permission_name`, `module_id`, `action_id`) VALUES
-- 超级权限
(1,  'ROOT',              0, 0),
-- 组织管理模块（ORG）
(2,  'ORG:SELECT',        1, 4),
(3,  'ORG:INSERT',        1, 1),
(4,  'ORG:UPDATE',        1, 3),
(5,  'ORG:DELETE',        1, 2),
-- 医护管理模块（MEDICAL）
(6,  'MEDICAL:SELECT',    2, 4),
(7,  'MEDICAL:INSERT',    2, 1),
(8,  'MEDICAL:UPDATE',    2, 3),
(9,  'MEDICAL:DELETE',    2, 2),
-- 出诊管理模块（SCHEDULE）
(10, 'SCHEDULE:SELECT',   3, 4),
(11, 'SCHEDULE:INSERT',   3, 1),
(12, 'SCHEDULE:UPDATE',   3, 3),
(13, 'SCHEDULE:DELETE',   3, 2),
-- 系统管理模块（SYSTEM）- 角色管理
(14, 'ROLE:SELECT',       4, 4),
(15, 'ROLE:INSERT',       4, 1),
(16, 'ROLE:UPDATE',       4, 3),
(17, 'ROLE:DELETE',       4, 2),
-- 系统管理模块（SYSTEM）- 用户管理
(18, 'USER:SELECT',       4, 4),
(19, 'USER:INSERT',       4, 1),
(20, 'USER:UPDATE',       4, 3),
(21, 'USER:DELETE',       4, 2),
-- 系统管理模块（SYSTEM）- 权限管理
(22, 'PERMISSION:SELECT', 4, 4);

-- ============================================================
-- 4. 清空并重建 role 表（角色表）
--    permissions: 当前角色拥有的权限ID集合
--    default_permissions: 系统内置权限（不可修改）
-- ============================================================
TRUNCATE TABLE `role`;

INSERT INTO `role` (`id`, `role_name`, `permissions`, `desc`, `default_permissions`, `systemic`) VALUES
(1, '超级管理员', '[1]', '超级管理员拥有所有权限', '[1]', 1),
(2, '医生', '[2, 6, 10]', '医生仅拥有查看权限', '[2, 6, 10]', 1),
(3, '运营', '[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]', '运营拥有组织管理、医护管理、出诊管理的增删改查权限', '[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]', 1);

-- ============================================================
-- 5. 更新 users 表的 role 字段，映射到新角色体系
--    角色1=超级管理员, 角色2=医生, 角色3=运营
-- ============================================================

-- 超级管理员用户（root=1）
UPDATE `users` SET `role` = '[1]' WHERE `id` = 1;   -- admin
UPDATE `users` SET `role` = '[1]' WHERE `id` = 2;   -- zhangsan

-- 运营用户
UPDATE `users` SET `role` = '[3]' WHERE `id` = 3;   -- lisi
UPDATE `users` SET `role` = '[3]' WHERE `id` = 4;   -- lisi1

-- 医生用户
UPDATE `users` SET `role` = '[2]' WHERE `id` = 18;  -- zhaoliu
UPDATE `users` SET `role` = '[2]' WHERE `id` = 19;  -- shunqi
UPDATE `users` SET `role` = '[2]' WHERE `id` = 20;  -- linan
UPDATE `users` SET `role` = '[2]' WHERE `id` = 21;  -- xiaowang

SET FOREIGN_KEY_CHECKS = 1;
