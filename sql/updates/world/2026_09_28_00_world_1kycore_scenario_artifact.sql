-- 1KYCore: apply final upstream scenario/artifact fixes after the 2026_09_27 batches.
-- Sources: sql/sylvania; upstream d4f9f5946a1a1c2ff8fd8aa04b2992828f63482c.

-- Source: rivage_scenarios_restore.sql
-- =====================================================================
-- Rivage brise : rendre a la carte 1460 son vrai scenario.
--
-- SIGNALE EN JEU : « la p1 ne se lance pas, le serveur considere
-- toujours la phase finale », et -- intuition juste de l'utilisateur --
-- « un cherry-pick a ete fait sur une autre session, ca a peut-etre
-- casse le scenario ».
--
-- C'etait bien cela. Les deux lots de correctifs repris le 27/09
-- (2026_09_27_00 et _01) contiennent tous deux :
--
--     DELETE FROM `scenarios` WHERE `map`=1460;
--     INSERT INTO `scenarios` VALUES (1460, 12, 1018, 1017);
--
-- Or 1018 « Broken Shore - Alliance » et 1017 « Broken Shore - Horde »
-- sont de TYPE 0 : une autre famille de scenarios. Notre implementation
-- vise le type 4, celui de la campagne d'introduction.
--
-- Verifie sur wago.tools, build 7.3.5.26972 :
--     786  « The Battle for Broken Shore », type 4, 9 etapes,
--          dont « Find Varian » et « Stop Gul'dan »   -> ALLIANCE
--     1189 « The Battle for Broken Shore », type 4, 9 etapes,
--          dont « Find The Others » et « Hold The Ridge » -> HORDE
--
-- L'etape « Raze the Black City » de 786 porte l'arbre 42770, celui-la
-- meme dont nous avons releve les poids (1, 2, 5, 10 pour 300 points).
--
-- Table lue au DEMARRAGE uniquement : un redemarrage est necessaire.
-- =====================================================================

DELETE FROM `scenarios` WHERE `map` = 1460;

INSERT INTO `scenarios` (`map`, `difficulty`, `scenario_A`, `scenario_H`, `zoneid`) VALUES
(1460, 12, 786, 1189, 0);


-- Source: rivage_pont_glace.sql
-- =====================================================================
-- Rivage brise, phase 7 : le pont de glace de Jaina.
--
-- VERIFIE SUR LA VIDEO : au bord du gouffre, Gelbin demande « Comment
-- est-ce qu'on va traverser ? », Jaina repond « Je m'en occupe » et gele
-- un passage. Le joueur le franchit a pied vers les Abords du tombeau.
--
-- Le modele officiel est identifie :
--   world/expansion06/doodads/brokenshore/7bs_brokenshore_icebridge01.m2
--   FileDataID 1349000, GameObjectDisplayInfo 35871
--
-- MESURE DECISIVE : ce modele ne porte AUCUNE collision -- zero triangle,
-- zero sommet, zero normale, lu directement dans son en-tete M2. Une
-- re-extraction des vmaps ne produirait donc rien : il n'y a rien a
-- extraire. Blizzard fait necessairement traverser ses joueurs autrement,
-- par du sol invisible ou un deplacement scripte.
--
-- On pose donc le visuel officiel, et dessous un plancher fait de
-- barrieres invisibles (affichage 6391), dont la collision, elle, est
-- bien presente dans notre index GameObjectModels.dtree.
--
-- Bords releves en jeu :
--   proche  (1415.93, 2134.50, 21.87)
--   lointain (1423.95, 2086.79, 35.86)
-- soit 48,38 m de portee et 13,98 m de denivele -- une pente de 16,1
-- degres, reprise dans le quaternion des dalles.
-- =====================================================================

DELETE FROM `gameobject_template` WHERE `entry` IN (1000200, 1000201);
INSERT INTO `gameobject_template`
  (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`ScriptName`) VALUES
(1000200, 5, 35871, 'Pont de glace', '', '', '', 1,   ''),
(1000201, 5,  6391, 'Plancher du pont de glace', '', '', '', 4.5, '');

DELETE FROM `gameobject` WHERE `guid` BETWEEN 210300200 AND 210300210;
INSERT INTO `gameobject`
  (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,
   `position_x`,`position_y`,`position_z`,`orientation`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,
   `spawntimesecs`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`) VALUES
-- Le visuel, au milieu du gouffre, couche dans son axe.
(210300200, 1000200, 1460, 0, 0, '12', 0, 0, 0, -1,
 1419.938, 2110.647, 28.866, 4.8789, 0, 0, 0.638140, 0.769920, 300, 100, 1, 0, '', 0),
-- Trois files de plancher invisible, inclinees a 16 degres.
(210300201, 1000201, 1460, 0, 0, '12', 0, 0, 0, -1,
 1417.7679, 2110.2824, 28.8663, 0.1665, -0.011658, 0.139734, 0.082323, 0.986692, 300, 100, 1, 0, '', 0),
(210300202, 1000201, 1460, 0, 0, '12', 0, 0, 0, -1,
 1419.9375, 2110.6470, 28.8663, 0.1665, -0.011658, 0.139734, 0.082323, 0.986692, 300, 100, 1, 0, '', 0),
(210300203, 1000201, 1460, 0, 0, '12', 0, 0, 0, -1,
 1422.1071, 2111.0115, 28.8663, 0.1665, -0.011658, 0.139734, 0.082323, 0.986692, 300, 100, 1, 0, '', 0);


-- Source: emmarel_dalaran.sql
-- Emmarel Shadewarden (102478) : ramenee a Dalaran.
--
-- Signalement d'un joueur : le PNJ a qui rendre la quete d'arme prodigieuse du
-- chasseur, a Dalaran, n'y est pas.
--
-- Verifie : l'entree 102478 est bien le point de rendez-vous de l'introduction aux
-- armes prodigieuses. Elle donne ET rend << Weapons of Legend >> (40618), et rend
-- aussi << The Hunter's Call >> (41415), << The Spear in the Shadow >> (40385),
-- << Needs of the Hunters >> (40384) et << Hunter to Hunter >> (40952, 41009).
-- Wowhead la place en zone 7502, Dalaran. Nous l'avions au Pavillon du tir
-- infaillible, avec les entrees 102574, 102578 et 107317 -- qui, elles, y sont bien
-- a leur place (zone 7877).
--
-- Position etablie par deux methodes independantes qui concordent :
--   X/Y : regression pin -> monde sur trente PNJ de Dalaran, les bornes de cette
--         zone etant nulles dans WorldMapArea.db2 -- Dalaran est une ville flottante.
--         Ses deux pins sont serres (2,9 m d'ecart), donc la position est nette.
--   Z   : les trois PNJ les plus proches du point calcule -- Koraud a 8,8 m, une
--         jardiniere a 6,4 m, Aerith Primrose a 11,2 m -- sont tous a 738,0. C'est
--         le niveau de la place principale.
--
-- L'orientation est arbitraire : aucune source ne la donne.
--
-- Annulation : db-backups/emmarel-dalaran-*.sql

UPDATE `creature`
   SET `position_x` = -868.50,
       `position_y` = 4395.90,
       `position_z` = 738.05,
       `orientation` = 3.1416,
       `zoneId` = 0,
       `areaId` = 0
 WHERE `guid` = 280000602 AND `id` = 102478;


-- Source: emmarel_choix_arme.sql
-- Emmarel Shadewarden (102478, Dalaran) : le chasseur ne pouvait pas choisir son arme prodigieuse.
-- Aucun gossip_menu_id : l option SmartAI (menu 19115) pour rouvrir le choix n apparaissait jamais,
-- et le script C++ npc_40618_artifact (option FR + choix a l acceptation) n etait rattache a rien.
-- Le SmartAI ne faisait rien d autre d utile (son Say LOS pointe vers un texte inexistant).
UPDATE creature_template SET AIName="", ScriptName="npc_40618_artifact" WHERE entry=102478;
DELETE FROM smart_scripts WHERE entryorguid=102478 AND source_type=0;

