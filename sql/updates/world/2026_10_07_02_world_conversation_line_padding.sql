-- Preserve the original opaque high word in the existing 16-byte conversation line packet.
-- Zero default retains every existing line. Do not assign undocumented client semantics.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_line_schema_guard`;
CREATE TEMPORARY TABLE `_1kycore_line_schema_guard` (ok INT PRIMARY KEY);
INSERT INTO `_1kycore_line_schema_guard` VALUES (1);
INSERT INTO `_1kycore_line_schema_guard` SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding' AND NOT (DATA_TYPE='smallint' AND COLUMN_TYPE LIKE '%unsigned' AND IS_NULLABLE='NO' AND (COLUMN_DEFAULT <=> '0') AND EXTRA='');
SET @ky_line_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding'), 'DO 0', 'ALTER TABLE conversation_line_template ADD COLUMN Padding SMALLINT UNSIGNED NOT NULL DEFAULT 0');
PREPARE ky_line_stmt FROM @ky_line_ddl;
EXECUTE ky_line_stmt;
DEALLOCATE PREPARE ky_line_stmt;
SET @ky_line_ddl = NULL;
DROP TEMPORARY TABLE `_1kycore_line_schema_guard`;
