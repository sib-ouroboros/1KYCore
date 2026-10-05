-- Quest 38727: C++ handles these personal destruction scenes.
-- Obsolete flag spells 191480/191519/191520 are absent in Legion 7.3.5 DB2.
UPDATE `gameobject_template` SET `Data10` = 0
WHERE `entry` IN (243965,243967,243968)
  AND `ScriptName` = 'go_mardum_illidari_banner'
  AND `Data10` IN (191480,191519,191520);
