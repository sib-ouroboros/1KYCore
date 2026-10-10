-- Read-only snapshot. Run against hotfix, not world/characters.
SELECT * FROM updates WHERE name LIKE '%broadcast_text_fr_dependencies%';
SELECT locale.ID,locale.locale,locale.VerifiedBuild FROM broadcast_text_locale locale LEFT JOIN broadcast_text base ON base.ID=locale.ID WHERE locale.locale='frFR' AND (locale.ID BETWEEN 132352 AND 132363 OR locale.ID=132367) AND base.ID IS NULL;
SELECT ID,Text,Text1,VerifiedBuild FROM broadcast_text WHERE ID BETWEEN 132352 AND 132363 OR ID IN(132367,36340,36341) ORDER BY ID;
