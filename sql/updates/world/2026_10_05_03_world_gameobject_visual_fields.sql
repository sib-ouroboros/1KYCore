-- Optional native GO visuals, zero by default; source quest-dependent visuals are not imported.
-- Reject conflicting pre-existing columns before any permanent DDL. Retry supports partial DDL.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_visual_schema_guard`;
CREATE TEMPORARY TABLE `_1kycore_visual_schema_guard` (ok INT PRIMARY KEY);
INSERT INTO `_1kycore_visual_schema_guard` VALUES (1);
INSERT INTO `_1kycore_visual_schema_guard` SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME='SpellVisualID' AND NOT (DATA_TYPE='int' AND COLUMN_TYPE LIKE '%unsigned' AND IS_NULLABLE='NO' AND (COLUMN_DEFAULT <=> '0') AND EXTRA='');
INSERT INTO `_1kycore_visual_schema_guard` SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME='SpellStateVisualID' AND NOT (DATA_TYPE='int' AND COLUMN_TYPE LIKE '%unsigned' AND IS_NULLABLE='NO' AND (COLUMN_DEFAULT <=> '0') AND EXTRA='');
INSERT INTO `_1kycore_visual_schema_guard` SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME='StateWorldEffectID' AND NOT (DATA_TYPE='int' AND COLUMN_TYPE LIKE '%unsigned' AND IS_NULLABLE='NO' AND (COLUMN_DEFAULT <=> '0') AND EXTRA='');
SET @ky_visual_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME='SpellVisualID'), 'DO 0', 'ALTER TABLE gameobject_template_addon ADD COLUMN SpellVisualID INT UNSIGNED NOT NULL DEFAULT 0');
PREPARE ky_visual_stmt FROM @ky_visual_ddl;
EXECUTE ky_visual_stmt;
DEALLOCATE PREPARE ky_visual_stmt;
SET @ky_visual_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME='SpellStateVisualID'), 'DO 0', 'ALTER TABLE gameobject_template_addon ADD COLUMN SpellStateVisualID INT UNSIGNED NOT NULL DEFAULT 0');
PREPARE ky_visual_stmt FROM @ky_visual_ddl;
EXECUTE ky_visual_stmt;
DEALLOCATE PREPARE ky_visual_stmt;
SET @ky_visual_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME='StateWorldEffectID'), 'DO 0', 'ALTER TABLE gameobject_template_addon ADD COLUMN StateWorldEffectID INT UNSIGNED NOT NULL DEFAULT 0');
PREPARE ky_visual_stmt FROM @ky_visual_ddl;
EXECUTE ky_visual_stmt;
DEALLOCATE PREPARE ky_visual_stmt;
SET @ky_visual_ddl = NULL;
DROP TEMPORARY TABLE `_1kycore_visual_schema_guard`;
