-- Restore The Raven's Eye252017 and Fel-Infused Gunpowder Cache267041.
-- Requires rebuilt go_campaign_rogue_interaction, source scene mappings08_05 and conversation08_06.
-- Source: LegionCore_world_735.26972_2024_10_23.sql, archive SHA256
-- cf681e1fb2e7443daab2a5db04f4efa2fc53cc485ea8de6b6ec3d60d569c2696.
-- Baseline: clean release b311837633e148df178045fd448cbaeb7e40d10b97690377866ce4560f68bac7.
-- Preserve spawns/phases and all user-modified templates; use the existing native GOOBER path.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_model_guard`, `_1kycore_model_baseline`, `_1kycore_model_source`, `_1kycore_model_addons`;
CREATE TEMPORARY TABLE `_1kycore_model_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_model_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_model_baseline` LIKE gameobject_template;
INSERT INTO `_1kycore_model_baseline` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`RequiredLevel`,`AIName`,`ScriptName`,`VerifiedBuild`) VALUES
(252017,0,0,'The Raven\'s Eye','','','',1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',0),
(267041,0,0,'Fel-Infused Gunpowder Cache','','','',1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',0);
CREATE TEMPORARY TABLE `_1kycore_model_source` LIKE gameobject_template;
INSERT INTO `_1kycore_model_source` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`RequiredLevel`,`AIName`,`ScriptName`,`VerifiedBuild`) VALUES
(252017,10,31225,'ÐžÐºÐ¾ Ð’Ð¾Ñ€Ð¾Ð½Ð°','questinteract','Usage','',2,93,0,0,1,0,0,0,0,0,0,219701,0,0,0,19700,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,'','go_campaign_rogue_interaction',22248),
(267041,10,15383,'Soaked in Fel Gunpowder','questinteract','ÐŸÐ¾Ð´Ð±Ð¾Ñ€','',1,1690,0,0,0,0,0,0,0,0,0,233370,0,0,0,125962,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,'','go_campaign_rogue_interaction',24015);

CREATE TEMPORARY TABLE `_1kycore_model_addons` LIKE gameobject_template_addon;
INSERT INTO `_1kycore_model_addons` (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`) VALUES
(252017,0,262144,0,0,0),
(267041,0,262144,0,0,0);

-- All checks run before any permanent write. Missing or customized rows reject.
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM `_1kycore_model_baseline` b JOIN `_1kycore_model_source` n ON n.entry=b.entry
LEFT JOIN gameobject_template t ON t.entry=b.entry
WHERE t.entry IS NULL OR (NOT ((t.`entry` <=> b.`entry`) AND (t.`type` <=> b.`type`) AND (t.`displayId` <=> b.`displayId`) AND (BINARY t.`name` <=> BINARY b.`name`) AND (BINARY t.`IconName` <=> BINARY b.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY b.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY b.`unk1`) AND (t.`size` <=> b.`size`) AND (t.`Data0` <=> b.`Data0`) AND (t.`Data1` <=> b.`Data1`) AND (t.`Data2` <=> b.`Data2`) AND (t.`Data3` <=> b.`Data3`) AND (t.`Data4` <=> b.`Data4`) AND (t.`Data5` <=> b.`Data5`) AND (t.`Data6` <=> b.`Data6`) AND (t.`Data7` <=> b.`Data7`) AND (t.`Data8` <=> b.`Data8`) AND (t.`Data9` <=> b.`Data9`) AND (t.`Data10` <=> b.`Data10`) AND (t.`Data11` <=> b.`Data11`) AND (t.`Data12` <=> b.`Data12`) AND (t.`Data13` <=> b.`Data13`) AND (t.`Data14` <=> b.`Data14`) AND (t.`Data15` <=> b.`Data15`) AND (t.`Data16` <=> b.`Data16`) AND (t.`Data17` <=> b.`Data17`) AND (t.`Data18` <=> b.`Data18`) AND (t.`Data19` <=> b.`Data19`) AND (t.`Data20` <=> b.`Data20`) AND (t.`Data21` <=> b.`Data21`) AND (t.`Data22` <=> b.`Data22`) AND (t.`Data23` <=> b.`Data23`) AND (t.`Data24` <=> b.`Data24`) AND (t.`Data25` <=> b.`Data25`) AND (t.`Data26` <=> b.`Data26`) AND (t.`Data27` <=> b.`Data27`) AND (t.`Data28` <=> b.`Data28`) AND (t.`Data29` <=> b.`Data29`) AND (t.`Data30` <=> b.`Data30`) AND (t.`Data31` <=> b.`Data31`) AND (t.`Data32` <=> b.`Data32`) AND (t.`RequiredLevel` <=> b.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY b.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY b.`ScriptName`) AND (t.`VerifiedBuild` <=> b.`VerifiedBuild`)) AND NOT ((t.`entry` <=> n.`entry`) AND (t.`type` <=> n.`type`) AND (t.`displayId` <=> n.`displayId`) AND (BINARY t.`name` <=> BINARY n.`name`) AND (BINARY t.`IconName` <=> BINARY n.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY n.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY n.`unk1`) AND (t.`size` <=> n.`size`) AND (t.`Data0` <=> n.`Data0`) AND (t.`Data1` <=> n.`Data1`) AND (t.`Data2` <=> n.`Data2`) AND (t.`Data3` <=> n.`Data3`) AND (t.`Data4` <=> n.`Data4`) AND (t.`Data5` <=> n.`Data5`) AND (t.`Data6` <=> n.`Data6`) AND (t.`Data7` <=> n.`Data7`) AND (t.`Data8` <=> n.`Data8`) AND (t.`Data9` <=> n.`Data9`) AND (t.`Data10` <=> n.`Data10`) AND (t.`Data11` <=> n.`Data11`) AND (t.`Data12` <=> n.`Data12`) AND (t.`Data13` <=> n.`Data13`) AND (t.`Data14` <=> n.`Data14`) AND (t.`Data15` <=> n.`Data15`) AND (t.`Data16` <=> n.`Data16`) AND (t.`Data17` <=> n.`Data17`) AND (t.`Data18` <=> n.`Data18`) AND (t.`Data19` <=> n.`Data19`) AND (t.`Data20` <=> n.`Data20`) AND (t.`Data21` <=> n.`Data21`) AND (t.`Data22` <=> n.`Data22`) AND (t.`Data23` <=> n.`Data23`) AND (t.`Data24` <=> n.`Data24`) AND (t.`Data25` <=> n.`Data25`) AND (t.`Data26` <=> n.`Data26`) AND (t.`Data27` <=> n.`Data27`) AND (t.`Data28` <=> n.`Data28`) AND (t.`Data29` <=> n.`Data29`) AND (t.`Data30` <=> n.`Data30`) AND (t.`Data31` <=> n.`Data31`) AND (t.`Data32` <=> n.`Data32`) AND (t.`RequiredLevel` <=> n.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY n.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY n.`ScriptName`) AND (t.`VerifiedBuild` <=> n.`VerifiedBuild`))) LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_template_addon a JOIN `_1kycore_model_addons` expected ON expected.entry=a.entry
WHERE a.faction<>expected.faction OR a.flags<>expected.flags OR a.mingold<>expected.mingold
OR a.maxgold<>expected.maxgold OR a.WorldEffectID<>expected.WorldEffectID LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_template t JOIN `_1kycore_model_source` n ON n.entry=t.entry
LEFT JOIN gameobject_template_addon a ON a.entry=t.entry
WHERE t.type=n.type AND a.entry IS NULL LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_questitem q JOIN `_1kycore_model_source` n ON n.entry=q.GameObjectEntry
WHERE q.ItemId<>0 LIMIT 1;

INSERT INTO `_1kycore_model_guard` SELECT 1 FROM gameobject_template_addon WHERE entry IN(252017,267041) AND (SpellVisualID<>0 OR SpellStateVisualID<>0 OR StateWorldEffectID<>0 OR SpellStateAnimID<>0) LIMIT 1;
-- All source credit, scene and conversation dependencies must already exist.
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=110470);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=117263);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_template WHERE ID=42680);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_template WHERE ID=45628);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_template WHERE ID=45629);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_objectives WHERE ID=285243 AND QuestID=42680 AND Type=0 AND ObjectID=110470 AND Amount=1);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_objectives WHERE ID=288227 AND QuestID=45628 AND Type=2 AND ObjectID=267041 AND Amount=1);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_objectives WHERE ID=288262 AND QuestID=45629 AND Type=2 AND ObjectID=267041 AND Amount=1);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM scene_template WHERE SceneId=1363 AND Flags=27 AND ScriptPackageID=1680 AND BINARY ScriptName=BINARY '');
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM scene_template WHERE SceneId=1547 AND Flags=20 AND ScriptPackageID=1784 AND BINARY ScriptName=BINARY '');
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM conversation_actor_template WHERE `Id` <=> 56913 AND `CreatureId` <=> 117263 AND `CreatureModelId` <=> 67721);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM conversation_line_template WHERE `Id` <=> 9723 AND `StartTime` <=> 0 AND `UiCameraID` <=> 133 AND `ActorIdx` <=> 0 AND `Flags` <=> 0 AND `Padding` <=> 0);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM conversation_line_template WHERE `Id` <=> 9724 AND `StartTime` <=> 9320 AND `UiCameraID` <=> 133 AND `ActorIdx` <=> 0 AND `Flags` <=> 0 AND `Padding` <=> 0);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM conversation_actors WHERE `ConversationId` <=> 4269 AND `ConversationActorId` <=> 56913 AND `ConversationActorGuid` <=> 0 AND `Idx` <=> 0);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM conversation_template WHERE `Id` <=> 4269 AND `FirstLineId` <=> 9723 AND `LastLineEndTime` <=> 22302 AND BINARY `ScriptName` <=> BINARY '');
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM conversation_actors WHERE ConversationId=4269 AND Idx<>0 LIMIT 1;
-- Preserve custom entry/GUID scripts, spell conditions and per-spawn script bindings.
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM smart_scripts WHERE source_type=1 AND (entryorguid IN(252017,267041) OR entryorguid IN(SELECT -CAST(guid AS SIGNED) FROM gameobject WHERE id IN(252017,267041))) LIMIT 1;
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM spell_script_names WHERE spell_id IN(219701,233370) LIMIT 1;
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM conditions WHERE SourceTypeOrReferenceId IN(13,17) AND SourceEntry IN(219701,233370) LIMIT 1;
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM gameobject WHERE id IN(252017,267041) AND BINARY ScriptName<>BINARY '' LIMIT 1;

-- Install missing source addons first; an addon-only interruption can retry.
INSERT INTO gameobject_template_addon (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`)
SELECT expected.`entry`,expected.`faction`,expected.`flags`,expected.`mingold`,expected.`maxgold`,expected.`WorldEffectID` FROM `_1kycore_model_addons` expected
LEFT JOIN gameobject_template_addon a ON a.entry=expected.entry WHERE a.entry IS NULL;

-- Rewrite only byte-compatible release placeholders; native rows stay intact.
UPDATE gameobject_template t JOIN `_1kycore_model_baseline` b ON b.entry=t.entry
JOIN `_1kycore_model_source` n ON n.entry=t.entry
SET t.`type`=n.`type`,t.`displayId`=n.`displayId`,t.`name`=n.`name`,t.`IconName`=n.`IconName`,t.`castBarCaption`=n.`castBarCaption`,t.`unk1`=n.`unk1`,t.`size`=n.`size`,t.`Data0`=n.`Data0`,t.`Data1`=n.`Data1`,t.`Data2`=n.`Data2`,t.`Data3`=n.`Data3`,t.`Data4`=n.`Data4`,t.`Data5`=n.`Data5`,t.`Data6`=n.`Data6`,t.`Data7`=n.`Data7`,t.`Data8`=n.`Data8`,t.`Data9`=n.`Data9`,t.`Data10`=n.`Data10`,t.`Data11`=n.`Data11`,t.`Data12`=n.`Data12`,t.`Data13`=n.`Data13`,t.`Data14`=n.`Data14`,t.`Data15`=n.`Data15`,t.`Data16`=n.`Data16`,t.`Data17`=n.`Data17`,t.`Data18`=n.`Data18`,t.`Data19`=n.`Data19`,t.`Data20`=n.`Data20`,t.`Data21`=n.`Data21`,t.`Data22`=n.`Data22`,t.`Data23`=n.`Data23`,t.`Data24`=n.`Data24`,t.`Data25`=n.`Data25`,t.`Data26`=n.`Data26`,t.`Data27`=n.`Data27`,t.`Data28`=n.`Data28`,t.`Data29`=n.`Data29`,t.`Data30`=n.`Data30`,t.`Data31`=n.`Data31`,t.`Data32`=n.`Data32`,t.`RequiredLevel`=n.`RequiredLevel`,t.`AIName`=n.`AIName`,t.`ScriptName`=n.`ScriptName`,t.`VerifiedBuild`=n.`VerifiedBuild`
WHERE (t.`entry` <=> b.`entry`) AND (t.`type` <=> b.`type`) AND (t.`displayId` <=> b.`displayId`) AND (BINARY t.`name` <=> BINARY b.`name`) AND (BINARY t.`IconName` <=> BINARY b.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY b.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY b.`unk1`) AND (t.`size` <=> b.`size`) AND (t.`Data0` <=> b.`Data0`) AND (t.`Data1` <=> b.`Data1`) AND (t.`Data2` <=> b.`Data2`) AND (t.`Data3` <=> b.`Data3`) AND (t.`Data4` <=> b.`Data4`) AND (t.`Data5` <=> b.`Data5`) AND (t.`Data6` <=> b.`Data6`) AND (t.`Data7` <=> b.`Data7`) AND (t.`Data8` <=> b.`Data8`) AND (t.`Data9` <=> b.`Data9`) AND (t.`Data10` <=> b.`Data10`) AND (t.`Data11` <=> b.`Data11`) AND (t.`Data12` <=> b.`Data12`) AND (t.`Data13` <=> b.`Data13`) AND (t.`Data14` <=> b.`Data14`) AND (t.`Data15` <=> b.`Data15`) AND (t.`Data16` <=> b.`Data16`) AND (t.`Data17` <=> b.`Data17`) AND (t.`Data18` <=> b.`Data18`) AND (t.`Data19` <=> b.`Data19`) AND (t.`Data20` <=> b.`Data20`) AND (t.`Data21` <=> b.`Data21`) AND (t.`Data22` <=> b.`Data22`) AND (t.`Data23` <=> b.`Data23`) AND (t.`Data24` <=> b.`Data24`) AND (t.`Data25` <=> b.`Data25`) AND (t.`Data26` <=> b.`Data26`) AND (t.`Data27` <=> b.`Data27`) AND (t.`Data28` <=> b.`Data28`) AND (t.`Data29` <=> b.`Data29`) AND (t.`Data30` <=> b.`Data30`) AND (t.`Data31` <=> b.`Data31`) AND (t.`Data32` <=> b.`Data32`) AND (t.`RequiredLevel` <=> b.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY b.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY b.`ScriptName`) AND (t.`VerifiedBuild` <=> b.`VerifiedBuild`);
DROP TEMPORARY TABLE `_1kycore_model_guard`, `_1kycore_model_baseline`, `_1kycore_model_source`, `_1kycore_model_addons`;
