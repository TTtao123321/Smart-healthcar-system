-- ============================================
-- 迁移脚本：移除 doctor_price.price_2
-- 适用场景：
-- 1. 新环境初始化时，确保旧列不会继续保留
-- 2. 已有环境升级时，可单独执行本脚本完成表结构迁移
-- ============================================

SET @drop_price_2_sql = (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'doctor_price'
        AND COLUMN_NAME = 'price_2'
    ),
    'ALTER TABLE `doctor_price` DROP COLUMN `price_2`',
    'SELECT ''doctor_price.price_2 already absent'' AS migration_status'
  )
);

PREPARE drop_price_2_stmt FROM @drop_price_2_sql;
EXECUTE drop_price_2_stmt;
DEALLOCATE PREPARE drop_price_2_stmt;
