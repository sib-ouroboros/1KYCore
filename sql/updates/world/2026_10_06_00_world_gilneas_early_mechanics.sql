-- Existing C++ implementations; audited against DB735.02 and local release.
-- Children class names retain legacy spelling, but entry/credit assignments are explicit.
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_horrid_abomination_36231', `KillCredit1`=0, `KillCredit2`=0
WHERE `entry`=36231 AND `ScriptName` IN ('','npc_horrid_abomination_36231');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_cynthia_36267', `npcflag`=(`npcflag` & ~16777216) | 1
WHERE `entry`=36287 AND `ScriptName` IN ('','npc_cynthia_36267');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_ashley_36269', `npcflag`=(`npcflag` & ~16777216) | 1
WHERE `entry`=36288 AND `ScriptName` IN ('','npc_ashley_36269');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_james_36268', `npcflag`=(`npcflag` & ~16777216) | 1
WHERE `entry`=36289 AND `ScriptName` IN ('','npc_james_36268');

-- Client group385 spans phases169-188; use the quest-specific phase instead.
-- These barrels serve quest14348 in phase182; never make all quest objects phase0.
UPDATE `gameobject` SET `PhaseId`=182, `PhaseGroup`=0
WHERE `id`=196403 AND `map`=654 AND `guid` IN (51003243,51003245,51003246,51003247,51003248,51003249,51003250,51003251,51003252,51003253)
    AND `PhaseId`=0 AND `PhaseGroup`=0;

-- Remove only the verified near-identical Liam duplicate, retaining the questgiver.
DROP TEMPORARY TABLE IF EXISTS `gilneas_duplicate_liam`;
CREATE TEMPORARY TABLE `gilneas_duplicate_liam` (`guid` BIGINT UNSIGNED PRIMARY KEY);
INSERT INTO `gilneas_duplicate_liam`
SELECT duplicate.`guid` FROM `creature` duplicate INNER JOIN `creature` retained ON retained.`guid`=801338
WHERE duplicate.`guid`=801588 AND duplicate.`id`=36140 AND retained.`id`=36140
    AND duplicate.`map`=654 AND retained.`map`=654 AND duplicate.`PhaseId`=182 AND retained.`PhaseId`=182
    AND duplicate.`PhaseGroup`=0 AND retained.`PhaseGroup`=0
    AND ABS(duplicate.`position_x`-retained.`position_x`)<1 AND ABS(duplicate.`position_y`-retained.`position_y`)<1
    AND ABS(duplicate.`position_z`-retained.`position_z`)<1;
DELETE a FROM `creature_addon` a INNER JOIN `gilneas_duplicate_liam` d ON d.`guid`=a.`guid`;
DELETE e FROM `game_event_creature` e INNER JOIN `gilneas_duplicate_liam` d ON d.`guid`=e.`guid`;
DELETE p FROM `pool_creature` p INNER JOIN `gilneas_duplicate_liam` d ON d.`guid`=p.`guid`;
DELETE s FROM `smart_scripts` s INNER JOIN `gilneas_duplicate_liam` d ON s.`entryorguid`=-CAST(d.`guid` AS SIGNED) WHERE s.`source_type`=0;
DELETE f FROM `creature_formations` f INNER JOIN `gilneas_duplicate_liam` d
    ON f.`leaderGUID`=d.`guid` OR f.`memberGUID`=d.`guid`;
DELETE c FROM `creature` c INNER JOIN `gilneas_duplicate_liam` d ON d.`guid`=c.`guid`;
DROP TEMPORARY TABLE `gilneas_duplicate_liam`;
