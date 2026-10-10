-- Restore 13 real Legion base records referenced by existing frFR translations.
-- Source: LegionCore_hotfixes_735.26972_2024_10_23.sql; build26124 rows.
-- SHA256: 437ef854f35dff7cb39cb34766769cec1b113a00a5f513361d3a8fcc6e48a96f
-- No locale deletion or replacement; retain existing custom base records atomically.
INSERT INTO broadcast_text (`ID`,`Text`,`Text1`,`EmoteID1`,`EmoteID2`,`EmoteID3`,`EmoteDelay1`,`EmoteDelay2`,`EmoteDelay3`,`EmotesID`,`LanguageID`,`Flags`,`ConditionID`,`SoundEntriesID1`,`SoundEntriesID2`,`VerifiedBuild`) VALUES
(132352,'Focus your mind. Remember your training.','',0,0,0,0,0,0,0,0,0,0,87858,0,26124),
(132353,'','Arator! Turalyon!?',0,0,0,0,0,0,0,0,0,0,0,87496,26124),
(132354,'The Void shows only half truths. Trust your instincts.','',0,0,0,0,0,0,0,0,0,0,87859,0,26124),
(132355,'','I can\'t-- I-- Argh!',0,0,0,0,0,0,0,0,0,0,0,87497,26124),
(132356,'','I won\'t let you! I am not yours to claim!',0,0,0,0,0,0,0,0,0,0,0,87498,26124),
(132357,'','Begone, wretched darkness.',0,0,0,0,0,0,0,0,0,0,0,87499,26124),
(132358,'Fight, curse you!','',0,0,0,0,0,0,0,0,0,0,87860,0,26124),
(132359,'Be sure to collect our prize, fleshling. I will tend to Alleria.','',0,0,0,0,0,0,0,0,0,0,87861,0,26124),
(132360,'The heart of a demigod. This is no mere token, Alleria.','',0,0,0,0,0,0,0,0,0,0,87862,0,26124),
(132361,'Take it, and you will be one step closer to your destiny.','',0,0,0,0,0,0,0,0,0,0,87863,0,26124),
(132362,'','I understand. Thank you. Both of you.',0,0,0,0,0,0,0,0,0,0,0,87500,26124),
(132363,'','It\'s... cold.',0,0,0,0,0,0,0,0,0,0,0,87501,26124),
(132367,'They are closing in. Ready yourself, $p.','',0,0,0,0,0,0,0,0,0,0,86180,0,26124)
ON DUPLICATE KEY UPDATE ID=broadcast_text.ID;
