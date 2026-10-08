-- Preserve the source AnimationData ID in the native GAMEOBJECT_STATE_ANIM_ID field.
-- Zero default retains every existing line. Do not assign undocumented client semantics.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_animation_schema_guard`;
CREATE TEMPORARY TABLE `_1kycore_animation_schema_guard` (ok INT PRIMARY KEY);
INSERT INTO `_1kycore_animation_schema_guard` VALUES (1);
INSERT INTO `_1kycore_animation_schema_guard` SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME='SpellStateAnimID' AND NOT (DATA_TYPE='int' AND COLUMN_TYPE LIKE '%unsigned' AND IS_NULLABLE='NO' AND (COLUMN_DEFAULT <=> '0') AND EXTRA='');
SET @ky_animation_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME='SpellStateAnimID'), 'DO 0', 'ALTER TABLE gameobject_template_addon ADD COLUMN SpellStateAnimID INT UNSIGNED NOT NULL DEFAULT 0');
PREPARE ky_animation_stmt FROM @ky_animation_ddl;
EXECUTE ky_animation_stmt;
DEALLOCATE PREPARE ky_animation_stmt;
SET @ky_animation_ddl = NULL;
DROP TEMPORARY TABLE `_1kycore_animation_schema_guard`;
