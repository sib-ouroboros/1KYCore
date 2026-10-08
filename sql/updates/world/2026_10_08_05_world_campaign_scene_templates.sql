-- Source spell_scene mappings for campaign spells 219701 and 233370.
-- Pinned LegionCore 22bfd97d0e0e30d215e408eb4da2b0419d8f00e7.
-- Source CustomDuration=0, ScriptName=NULL, no spell_scene_event rows.
-- Do not replace custom mappings. Rebuilt worldserver includes scene lifecycle fixes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_scene_templates`;
CREATE TEMPORARY TABLE `_1kycore_scene_templates` (
 `SceneId` INT UNSIGNED NOT NULL PRIMARY KEY,
 `Flags` INT UNSIGNED NOT NULL,
 `ScriptPackageID` INT UNSIGNED NOT NULL,
 `ScriptName` VARCHAR(64) NOT NULL
);
INSERT INTO `_1kycore_scene_templates` VALUES
 (1363,27,1680,''),
 (1547,20,1784,'');
DROP TEMPORARY TABLE IF EXISTS `_1kycore_scene_guard`;
CREATE TEMPORARY TABLE `_1kycore_scene_guard` (`id` INT NOT NULL PRIMARY KEY);
INSERT INTO `_1kycore_scene_guard` VALUES (1);
INSERT INTO `_1kycore_scene_guard`
SELECT 1 FROM `scene_template` current
JOIN `_1kycore_scene_templates` source ON current.SceneId=source.SceneId
WHERE NOT (current.Flags <=> source.Flags)
 OR NOT (current.ScriptPackageID <=> source.ScriptPackageID)
 OR NOT (BINARY current.ScriptName <=> BINARY source.ScriptName)
LIMIT 1;
INSERT INTO `scene_template` (`SceneId`,`Flags`,`ScriptPackageID`,`ScriptName`)
SELECT source.SceneId,source.Flags,source.ScriptPackageID,source.ScriptName
FROM `_1kycore_scene_templates` source
WHERE NOT EXISTS (SELECT 1 FROM `scene_template` current WHERE current.SceneId=source.SceneId);
DROP TEMPORARY TABLE `_1kycore_scene_guard`;
DROP TEMPORARY TABLE `_1kycore_scene_templates`;
