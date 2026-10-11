-- 24468 now counts five distinct survivor conversations, not slain crocodiles.
-- Retain amount, storage, descriptions and other objectives.
UPDATE quest_objectives SET ObjectID=37067
WHERE ID=255768 AND QuestID=24468 AND Type=0 AND ObjectID=37078 AND Amount=5 AND StorageIndex=0;
