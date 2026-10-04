# Матрица загрузчиков и семантики

Аудит по стартовому SHA из sources.json, изменения C++ отдельно описаны в ревью.
Fallback `ObjectMgr::GetLocaleString`: локализованная непустая строка заменяет базовую;
пустая/отсутствующая оставляет базовый текст. Локаль берётся из конкретной сессии.

| Категория | Целевая таблица/ключ | Поля и маршрут | Донор/решение |
|---|---|---|---|
| Quest template | quest_template_locale, ID+locale | 9 полей; ObjectMgr:4949, Quest/Query и GossipDef | ID, LogTitle, QuestType, QuestSortID и конкретный English exact |
| Reward | quest_offer_reward_locale, ID+locale | RewardText; ObjectMgr:5079, GossipDef:630–649 | V2 OfferRewardText → RewardText; base RewardText и родитель quest exact |
| Request items | quest_request_items_locale, ID+locale | CompletionText; GossipDef:696–705 | конкретный English и родитель quest exact |
| Objectives | quest_objectives_locale, ID+locale | Description; ObjectMgr:4996 | QuestID, Type, ObjectID, Amount, StorageIndex; source locale QuestId/StorageIndex; parent quest |
| NPC | creature_template_locale, entry+locale | Name, NameAlt, Title, TitleAlt; QueryHandler:119–126 | creature_template_wdb_locale Name1/NameAlt1/Title/TitleAlt; base name/type/family; Name2–4 не переносятся |
| Objects | gameobject_template_locale, entry+locale | name, castBarCaption; QueryHandler:152–158 | locales_gameobject name_loc8/castbarcaption_loc8; English name/type; Unk1 не доказан |
| Books | page_text_locale, ID+locale | Text; QueryHandler:269–272 | English каждой страницы и цепочки NextPageID; cycles/missing chain → manual |
| Choices | playerchoice_locale ChoiceId+locale | Question; ObjectMgr:10946 | base Question exact |
| Responses | playerchoice_response_locale ChoiceId+ResponseId+locale | Header, Answer, Description, Confirmation | base Index + unique variant; base PK имеет дополнительный Index, ambiguity → manual |
| Direct gossip | gossip_menu_option_locale MenuId+OptionIndex (Locale НЕ входит в PK) | OptionText, BoxText; ObjectMgr:357; GossipDef:99–124 | V2 MenuID+ID+Locale → MenuId+OptionIndex+Locale, ID подтверждён GossipData.cpp; owner NPC/name, English, type/icon/flags/action/confirmation |
| Signposts | points_of_interest_locale ID+locale | Name; ObjectMgr:389, GossipDef:298–301 | locales_points_of_interest icon_name_loc8; English, coordinates/icon/flags/importance exact; 0 compatible |
| Creature speech | creature_text_locale CreatureID+GroupID+ID+Locale | CreatureTextMgr:179,445–456 | нет donor creature_text_locale; direct base text не является русским locale-донором |
| NPCText | npc_text ID, BroadcastTextID0–7 | QueryHandler отправляет вероятности и Broadcast ID | нет runtime locale-table Text0_* в target; V2 locales_npc_text не импортируется в исчезнувший путь |
| Broadcast/hotfix | broadcast_text_locale ID+locale | Text_lang/Text1_lang; HotfixDatabase:212, DB2Stores:1525 | обе English gender формы exact; runtime gender/fallback нативный |
| Server strings | trinity_string entry, content_loc8 | ObjectMgr:8462; WorldSession:764; ChatHandler | content_default exact + полный printf signature; content_default/loc1–7 не меняются |
| C++ literals | scripted menu/messages | отдельная очередь audit_cpp.py | только подтверждённая существующая запись 27602; не механический перевод всех литералов |

Для gossip английский BoxText и действия берутся из target вспомогательных
gossip_menu_option_box/action, а у донора из основной таблицы. Присутствие/отсутствие
вспомогательных строк защищено runtime-guard. OptionNPC в доноре — icon, что
подтверждается загрузчиком; не путать с владельцем NPC. Владельцы независимо
сопоставлены по creature_template.gossip_menu_id и английскому имени WDB.
Несовпавшие OptionNpcflag2/BoxCurrency не адаптируются. Foreign Locale, уже занявшая
PK target, сохраняется целиком. Пункты без доказанного owner остаются manual.

BroadcastText имеет приоритет над direct gossip/CreatureText locale, если запись
существует в sBroadcastTextStore. Поэтому direct поле с ненулевым Broadcast ID
не импортируется даже при одинаковом English: его правильный маршрут — hotfix.
CreatureTextMgr выбирает native Broadcast Text по полу, затем direct fallback.
Русский голос использует существующие Sound/Voice ресурсы клиента; ID звуков не менялись.

DB2Stores сначала читает основной DB2, LoadFromDB накладывает hotfix/base в enUS,
затем загружает строки default locale, дополнительные файлы и включённые hotfix
локали. Hotfix SELECT не фильтрует VerifiedBuild. Нет оснований проставлять 26972
донорскому тексту. Остальные DB2/hotfix-locales (items/spells/achievements и т.п.)
не включены в allowlist: нужны независимое сопоставление назначения/layout/English;
их покрытие не выдаётся за измеренное и донорские IDs не заменяются массово.

Quest greeting/achievement reward и прочие locale-пути остаются отдельной очередью:
от основного донора не подтверждены соответствующие переводы для этой схемы.
Существующие записи и маршруты не менялись. Приоритет следующего ручного разбора:
Legion intro/DH start/class halls/artifacts/Suramar/Broken Shore/Argus, затем старые
зоны. Для подтверждённых allowlist импорт выполнен целиком независимо от порядка
ID; диапазоны ID не использовались как доказательство зоны или доступности.

Для стабильной проверки всех категорий предусмотрен перезапуск тестового worldserver.
Hotfix/DB2 нельзя считать проверенными одним SQL reload. Клиент может кешировать
названия/страницы/quest query: при устаревшем отображении использовать чистую
тестовую сессию и штатную очистку Cache/WDB остановленного клиента с резервной
копией кеша. Не удалять Data/DB2 клиента ради очистки кеша.
