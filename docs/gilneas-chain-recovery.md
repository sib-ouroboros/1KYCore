# Восстановление цепочки Гилнеаса

## Исходное состояние и границы проверки

ТЗ от 06.10.2026, база кода `46f85bb407de11e77c2dd235264b94fce9fd685e`, ветка `feature/npc-crowd-separation`. Аудит выполнен до изменений поведения. Прочитана локальная копия world релиза 1KYCore; это не рабочая база Linux. Дополнительно извлечён и прочитан оригинальный DB735.02; исторические INSERT не выполнялись. Миграции проверяются на фактических структурах локального релиза. Клиентские DB2 доступны для 26654, целевой клиент 26972: совпадение layout не равнозначно полному совпадению контента. Полное прохождение 26972 выполняет пользователь после подготовки. До него статус FIXED для всей цепочки не используется.

Проверены 88 зарегистрированных классов трёх поздних файлов, 77 связанных шаблонов NPC, 727 спавнов и 15 спавнов GO из первоначального набора. Прочитаны quest_template/addon/objectives/POI, шаблоны и addon NPC/GO, queststarter/ender, SmartAI, conditions, spell hooks, spellclick, linked spells, spell_area и маршруты. Полный снимок хранится отдельно от репозитория в рабочем артефакте; отчёт ниже содержит существенные результаты.

SylvaniaCore проверен на `cd8dd5c` после fetch. `zone_gilneas_city2.cpp` и `zone_gilneas_city3.cpp` совпадают. Отличия `zone_duskhaven.cpp` — прежние локальные исправления сцены 14375; готового upstream-исправления описанных поздних ошибок не обнаружено. Файлы целиком не переносились.

Категории: A — отсутствующий спавн; B — фаза; C — привязка; D — ошибка C++; E — отсутствующая реализация; F — несколько причин. Категория относится к установленным дефектам и ещё проверяемым причинам симптома, а не к доказанному клиентскому воспроизведению.

## Первый аудит до реализации

| Quest | Симптом из ТЗ / данные | C++ | ScriptName / spell hook | Spawn | Фаза | Категория / причина | Статус |
|---|---|---|---|---|---|---|---|
| 14336 | Два Liam | Специальный AI не нужен | Questgiver 36140 | GUID 801338 и 801588, менее 1 м | Оба 182 | B: настоящий дубль в одной фазе, не два сюжетных этапа | PARTIALLY FIXED: аудит |
| 14348 | Бочки/зачёт | Да | 36231 без C++; hook 69094 есть | 10 бочек есть | Бочки phase/group=0 | F: любой SpellHit выдаёт credit в C++; неправильная фазировка бочек; требуются взрыв и цепочка ForceCast | PARTIALLY FIXED: аудит |
| 14386 | Не виден NPC | Да | 36409/36405 не привязаны | Подлежит сопоставлению стадий | 182 | F: отсутствующий AI; видимость Thyala проверяется отдельно | PARTIALLY FIXED: аудит |
| 14368 | Дети не реагируют | Да | Пустой ScriptName, SmartAI без полезной реализации | Все трое есть | 182 | F: классы названы 36267/68/69; Ashley/James credits перепутаны; spellclick и gossip конкурируют | PARTIALLY FIXED: аудит |
| 14395 | Нельзя поднять | Да | Нет AI/hook68735; spellclick cast_flags=0 | Есть | Нужна сверка стадии | F: неверное направление spellclick, отсутствующий hook; credit36440 в альтернативной ветке не совпадает с objective36450 | PARTIALLY FIXED: аудит |
| 14399 | Нет книги | Нативный loot | Специальный AI не нужен | Нет | Нужен подтверждённый источник | A: template/loot49280 есть, spawn отсутствует | PARTIALLY FIXED: аудит |
| 14416 | Нет доставки | Да | Оба AI и hook68903 отсутствуют | Есть | Проверяется с Лорной | F: ошибочный enum54416, отсутствующий hook, нет защиты от повторной/чужой высадки | PARTIALLY FIXED: аудит |
| 14404 | Нет материалов | Нативный loot | Специальный AI не нужен | 196808/809 отсутствуют; инструменты196810 установлены по loot49337 | Нужен источник координат | A: три предмета49337/38/39, шаблоны/loot существуют | PARTIALLY FIXED: аудит |
| 14400 | Только GM | Нативный loot | Специальный AI не нужен | 196472 есть | Подлежит сверке spell_area183 | B: не снимать фазы глобально | NOT REPRODUCED: клиент |
| 14401 | Нет события Chance | Да, proximity | AI36459 отсутствует | Есть | Проверяется | C: сначала восстановить существующую сцену; shared owner отдельно | PARTIALLY FIXED: аудит |
| 14465 | Поездка/видимость | Да | Gwen/horse не привязаны; GO hooks есть | Есть | Нет правил184 в Гилнеасе; маршруты проверяются | F: bindings + фаза/маршрут, не заменять телепортом | PARTIALLY FIXED: аудит |
| 24438 | Нет дилижанса | Да | 44928/43336/43337 без ScriptName | Проверяются persistent и summons | Проверяется | F: bindings + данные маршрута; script_waypoint для IDs пуст | PARTIALLY FIXED: аудит |
| 24468 | Гибнут survivors | Да | Оба AI отсутствуют | Есть | 186 | C: фильтры урона не выполняются без bindings; objective — убийства37078, не survivor credit | PARTIALLY FIXED: аудит |
| 24472 | Нет знамени | Да | GO201594 уже привязан | Нет | Нужен источник | A: существующий template/loot49742 без spawn | PARTIALLY FIXED: аудит |
| 24495 | Нет страниц | Нативный loot | Специальный AI не нужен | Нет | Нужен источник | A: objective49760 ×6, template/loot есть | PARTIALLY FIXED: аудит |
| 24627 | Высокие уровни | Есть общий бой | 37757 SmartAI | Проверяется область | Проверяется scaling | Пока D/B не доказаны: min5/max20 может быть Legion scaling; глобально уровни не менять | NOT REPRODUCED |
| 24628 | Нет Moonleaf | Нативный loot | Специальный AI не нужен | Нет | Нужен источник | A: objective50017 ×6, template/loot есть | PARTIALLY FIXED: аудит |
| 24646 | Рог не помогает | Нет специального horn script в зоне | Проверяется item50134 | Нужны союзники и coffer201939 | Проверяется | E/A: цель — предмет50086; реализация horn требует подтверждённых spells/entries | PARTIALLY FIXED: аудит |
| 24593 | Источники/Two Forms | PlayerScript есть | Gate14375, reward72829 | 201950/951/952 отсутствуют | Проверяется | F: отсутствующие GO, gate требует исследования reward chain и AddSpell | PARTIALLY FIXED: аудит |
| 24592 | Stealth/drunk/Genn | Да для Genn | 37876 не привязан; Walden SmartAI75359 | Проверяется | В Gilneas нет spell_area187 | F: binding, стадия, spell75359 требует проверки duration; не делать всех пассивными | PARTIALLY FIXED: аудит |
| 24575 | Не работают цепи | Да | Villager без AI; GO уже привязан | GO201775 отсутствуют | Проверяется | F: A/C + shared owner, nearest villager selection; objective GO201775 ×5 | PARTIALLY FIXED: аудит |
| 24904 | Пустая битва | Большая реализация есть | Основные city2 bindings есть | >100 связанных боевых спавнов есть | Армия187, Krennan186 | B/F: нельзя считать армию отсутствующей; переход и shared scene проверяются | PARTIALLY FIXED: аудит |
| 24902 | Нет companion/сцены | city3 Tobias38507/Sylvanas38530 | Проверяется | Эти entries отсутствуют в исходном наборе спавнов | Проверяется | A/F: существующая сцена требует actors, ownership и routes | PARTIALLY FIXED: аудит |
| 24920 | Не работает bat | Да | Spells72247/72849 привязаны | Bat38540 не найден | Маршруты3854001/02 отсутствуют | A/F: транспортные данные; цели38287 ×6/38363 ×40 | PARTIALLY FIXED: аудит |
| 24678 | Крысы/выход | Спецреализации нет | Rat37889 без AI | Проверяется | Нужен questender | E/B не доказаны полностью: delivery quest без kill objective; torch должен отпугивать, не давать выдуманный credit | PARTIALLY FIXED: аудит |

## Ограничения источников

Автоматически угадывать NPC entry по числу в имени класса нельзя: `npc_trigger_quest_24616` заканчивается quest ID, а creature24616 — Mammoth Patriarch. Такая привязка запрещена. Аналогично старые имена детских классов не соответствуют реальным NPC36287/88/89.

`spell_area` 68481–69485 используется также в Дреноре, areas7037–7129. Нельзя удалять строки по одному spell ID или исправлять все зоны одновременно. Существующие ранние миграции 01.10 и 05.10 учитываются отдельно от исходной копии дампа: их повторная публикация не считается новым исправлением.

Исторические SQL не импортированы. Из них извлекаются только проверенные записи с указанием файла/строки; SmartAI-варианты и телепорты вместо транспорта не переносятся.

## Приёмка пользователем

Новый ворген, обычный аккаунт, клиент26972, без GM. Для каждой строки таблицы: accept → POI → видимость NPC/GO → interaction → правильный objective → complete → reward → следующий quest и фаза. Повторить релог, restart, смерть, abandon/reaccept и двух игроков. Фазы не исправлять вручную. Для поездок проверить посадку, реальный маршрут, ворота и высадку. Для 14348 сравнить правильную бочку с произвольным заклинанием; для детей — повторный разговор с одним ребёнком; для 14395/14416 — владельца, доставку и повторную попытку; для 24904 — сохранность ключевых actors и продолжение после смерти trash.

## Журнал реализации

До получения клиентских результатов ни одна сцена не объявляется полностью FIXED. Здесь будут указаны отдельные проверенные изменения, SQL, native/MySQL тесты и ещё оставшиеся ограничения.

### Подготовленный пакет 06.10.2026

- 14336: удаляется только проверенный дубль Liam801588 рядом с сохраняемым801338, вместе с зависимостями этого GUID. Сюжетные варианты в других фазах сохраняются.
- 14348: зачёт36233 только от предметного spell69094, правильного игрока и незавершённого задания; одна бочка на мерзость, штатный взрыв68560 через3 секунды. Native ForceCast подавлен, чтобы не помещать ауру68555 на игрока. Десять бочек ограничены фазой182 вместо нулевой.
- 14368: восстановлены gossip-привязки трёх детей36287/36288/36289, исправлены Ashley/James и objective slots. Повторный разговор не даёт повторный credit.
- 14395: восстановлены AI/watchman, spellclick направление player→NPC и hook68735. Запрещено забрать уже переносимого NPC или занять заполненное место. Проверяются владелец, живой игрок, задание и берег рядом с Liam; credit36450, не36440. Отмена/смерть/потеря владельца не засчитывает доставку.
- 14416: исправлен quest ID54416→14416, восстановлены два horseAI и hook68903. Ранняя/чужая высадка не засчитывает доставку. Нативный68903→68908 не дублируется linked_spell.
- 24468 и фон Haywards: восстановлены существующие AI37067/37078/36488, чтобы выполнялись штатные фильтры NPC-урона. Не введены новые credits survivors или глобальные изменения агрессивности.
- 14399/14404/24472/24495/24628/24593 и объекты24575/24646: добавлены95 спавнов12 типов GO. Координаты из Preservation SQL, фаза183/186 сопоставлена с текущими questenders; старый phaseMask не переносится. Это восстановление данных, а не подтверждение всей сцены24575 или horn24646.
- Two Forms: фактическая наградная цепочка24593→72829→72857→68996 подтверждена DB2. Исправлены gate в Player::AddSpell и custom PlayerScript. Повторный вход восстанавливает отсутствующее заклинание после награды; уже сохранённые ранние способности не отнимаются. Существующий bypass loading/level25 сохранён.

SQL: `2026_10_06_00`, `01`, `02` (world). Сначала применяются обычные обновления репозитория, затем этот пакет. Автообновлятор world использует существующий порядок файлов; никаких действий с рабочим сервером не выполнялось.

### Источники и проверка

Оригинальный [DB735.02](https://github.com/slash-design/DestinyCore/releases/tag/DB735.02): SHA256 архива `a887055dbe7cf939d48f23505400b1f615b05e5ef056f70ee322301eaad9374b`, world SQL `994bbbc4b911119b50d385d7c28876efb5a32baab22f0e944e86188b6f8e7292`. Проверены выбранные строки и DDL; он тоже не содержит нужные12 GO/маршруты поездок. [Preservation](https://github.com/The-Legion-Preservation-Project/LegionCore-7.3.5) используется как источник95 координат; точный SHA, исходные GUID и преобразованные строки находятся в `docs/audit-data/gilneas-static-restoration.json`. Все строки адаптированы к текущей схеме отдельно от исторической логики.

Локально PASS: реальные обработчики бочек/детей, спасения/посадки/отмены/чужого владельца/повторного зачёта и racial gate с GCC17, `-Wall -Wextra -Werror`; это компиляционные фикстуры production-фрагментов, не полноценный worldserver. На Windows запущены без sanitizers; Linux CI включает ASan/UBSan.

MySQL8.0.45 на изолированной копии релиза: первый импорт, повторный импорт без изменений,95 спавнов,10 привязок, направление spellclick, защита чужого GUID, отсутствие дубля при совпадающем спавне с другим GUID, сохранение пользовательского ScriptName/hook и checksum остальных таблиц — PASS. Прогон выявил и устранил MySQL1137 при повторном чтении временной таблицы. Подключён отдельный CI suite `--gilneas-chain-only`.

### Ещё не завершено

Полный пакет25 заданий не готов к объявлению FIXED. Текущие изменения представлены ниже; первоначальный аудит не является перечнем остатка. Для дальнейшей реализации остаются escort24902 (достоверных маршрутов3850701…05 нет), multiplayer battle24904, полная сцена Grandma14401 и Godfrey24592. Подготовленные механики/объекты/фазы/транспорт требуют прохождения26972. Уровни37757 для24627 не изменены: min5/max20 сам по себе не доказывает ошибку Legion scaling. Для14400 нужен обычный клиентский тест с корректной фазой.

Историческая таблица выше остаётся записью аудита **до реализации**; этот журнал отражает выполненные изменения. Ни один автоматический тест не заменяет прохождение клиентом26972, особенно визуалы, геометрию новых GO и транспорта. Сборки текущего пакета учитываются отдельно от успешных старых сборокe06d7ca.

### Дополнение: переход14396,24592,24575,24678

`2026_10_06_03`: маска начала183 изменена64→74 только в10 известных Gilneas areas. При принятии14396 игрок больше не теряет одновременно182 и183. Привязка Godfrey36290 восстановлена. Native `SpellArea::IsFitToRequirements` проверен для accept/complete/reward, abandon/reaccept, состояния после relog и другой зоны; фактическое обновление клиентской видимости требует прохождения.

`2026_10_06_04`: Genn37876 защищён от урона фоновых NPC, только map654; игроки/питомцы и другие карты не затронуты. Повторная сдача разными игроками не ставит второй набор событий общей сцены. Hook75359 подавляет **только постоянный INEBRIATE** в атаке Walden37733 на участника24592 на map654. Нативные урон и4-секундный stun сохраняются. Временный пьяный визуальный эффект не восстановлен; это ограничение, а не полная Blizzlike реализация. Уже сохранённое опьянение не сбрасывается глобально.

`2026_10_06_05`: Half-Burnt Torch50220→70631 вызывает5-секундное бегство только37889/37891/37892 при активном24678 и map654. Другие targets не изменены; никаких kill credits.407 крыс,31 паук,14 личинок и questender38144 уже присутствуют в188. Причина их невидимости остаётся в фазовом переходе, новые массовые спавны не создавались. Назначение задания подтверждено [описанием Knee-Deep](https://www.wowhead.com/quest=24678/knee-deep); конкретные NPC/эффект проверены по текущей БД, оригинальному DB735.02 и DB2.

`2026_10_06_06`: восстановлена привязка существующего villagerAI37694;18 chainGO сопоставлены с18 пленными (0.77–1.16м, следующие NPC значительно дальше). Активный scene owner не перезаписывается вторым игроком; повторный DoAction не дублирует события, Reset очищает их. Исключено `DestroyForNearbyPlayers`: видимость/credit обслуживает нативный GO use. Villager respawn300s согласован с восстановленными chainGO. Реальное GO взаимодействие, анимации и совместный cooldown требуют клиентской приёмки; фикстура проверяет ownership, пару/дистанцию, quest gate, бегство, cleanup/respawn и отсутствие synthetic credit.

`audit_gilneas_bindings.py --snapshot <world-snapshot.json>` автоматически сопоставляет все зарегистрированные CreatureScript/GameObjectScript/SpellScriptLoader трёх файлов с template, spawn overrides и spell hooks. Без snapshot проверяет регистрации; `--require-all` возвращает ошибку при отсутствующих привязках. Числовые суффиксы классов не используются как entry. Снимок содержит массивы `creature_template`, `creature`, `gameobject_template`, `gameobject`, `spell_script_names` с исходными полями. MySQL suite дополнительно сверяет каждую новую привязку с реально зарегистрированным C++.

Свежий импорт опубликованного world архива обнаружил исторически перепутанные ScriptName детей, отсутствовавшие в ранее подготовленной локальной копии. Миграция исправляет только два известных варианта, сохраняя произвольные administrator bindings. Первые CI: native Reliability наbe3dc10 PASS; MySQL runner сначала исправлен после IndentationError, затем выявил эти legacy bindings. Старые результаты не считаются проверкой новых04–06.

Автоматический снимок после00–06:89 классов,65 с bindings,24 без них (`docs/audit-data/gilneas-binding-audit.json`). Это диагностика конкретной копии без повторного применения ранних01/05.10 migrations; например36331/36332 уже исправлены прежним05.10_04. Отсутствие binding не означает, что класс можно безопасно включить: небезопасные summons/transport/state требуют отдельного разбора. `--require-all` пока ожидаемо не проходит.

### Horn of Tal'doren24646

`2026_10_06_07`: item50134/spell71061 SEND_EVENT23338 не имел реализации. Новый hook вызывает ровно8 временных38027 на проверенных координатах105080–105087 из историческогоpart3 (записи не импортируются в creature). Шаблон faction2207 дружественен Alliance и враждебен ranger2213; нет global faction/AI изменений рейнджеров. Item cooldown60000ms сохраняется. Существующий отряд не позволяет создать второй, lifetime45000ms; завершение/отмена задания, смерть/выход/потеря фазы владельца удаляет союзников.

Область —80м от текущего coffer201939 (-2118.81,1630.49,-41.6281), активный24646, map654, живой игрок. Native spell targetsSelf, дополнительного killcredit нет. Рейнджеры38022 в той же фазе отвлекаются threat/AttackStart на союзников; уже ведущийся бой другого игрока или его временного отряда не перехватывается. Неправильные administrator faction/ScriptID отклоняются до summon. Spell71019 War Stomp сохранён. Внешний источник подтверждает необходимость дождаться боя союзников перед подходом к сундуку: [Take Back What's Ours](https://www.wowhead.com/quest=24646/take-back-whats-ours).

Native fixture проверяет действующий квест/карту/область, custom template, отсутствие рейнджеров, максимум8/lifetime, повторный вызов, чужую цель/отряд, cleanup по отмене/смерти/выходу. Реальные threat, бой/навигация и визуалы26972 остаются в клиентской приёмке.

CI для6fcd532: Reliability PASS (ASan/UBSan); MySQL gilneas-chain PASS на свежем релизе (00–06). GCC be3dc10 PASS; это не проверка более позднего Horn кода. Windows ещё выполнялся на момент записи.

### Grandma’s Cat14401

`2026_10_06_08`: взаимодействие с Chance36459 при активном14401 создаёт персонального Lucius36461. Повторное нажатие не создаёт второй экземпляр; разные игроки получают разных нападающих. Chance остаётся доступен другим игрокам. Lucius атакует владельца, исчезает при отмене/смерти/выходе/потере фазы, время жизни180s оставляет возможность забрать предмет с тела. Objective — item49281; существующая100% quest loot сохраняется, synthetic credit не используется. Native fixture проверяет двух игроков и cleanup после evade.

Источники: [Grandma’s Cat](https://www.wowhead.com/quest=14401/grandmas-cat), действующие quest_objectives/creature_loot_template и исходные координаты C++. В комментариях описана попытка подобрать кота и последующий бой. Перевоплощение/помощь бабушки и дополнительные способности Lucius пока не восстановлены: требуется отдельная проверка сцены, это не окончательная Blizzlike приёмка.

Локальные проверки07–08: native GCC `-Wall -Wextra -Werror` PASS; MySQL8.0.45 на изолированной копии — первичное/повторное применение00–08, чужие bindings/таблицы/фазы и native quest loot PASS. Windows полный build be3dc10 также PASS; новым07–08 нужна собственная полная сборка.

### To Greymane Manor14465

`2026_10_06_09`:28 точек реальной поездки из закреплённого открытого исходника перенесены только как координаты, `waypoints36741` → `waypoint_data3674101`. Provenance и SHA256 архива сохранены в `docs/audit-data/gilneas-horse-route-source.json`. Перед записью проверяется отсутствие конфликтующих точек; чужой маршрут вызывает ошибку и не меняется. Route/SQL идемпотентны. Восстановлены guarded bindings Gwen36452, horse36741 и Mia36606.

Отсутствие objectives у14465 в релизной БД проверено: native COMPLETE после accept не считается отсутствием задания. Horse принимает только владельца, seat0, active INCOMPLETE/COMPLETE, map654. Высадка — только последняя28-я точка, прежняя11-я больше не обрывает поездку. Раннее спешивание не создаёт synthetic quest credit; завершение задания остаётся нативным. Cleanup: отмена, смерть, выход, потеря пассажира и предел360s.

Native phase18469077 восстанавливается двумя известными правилами part2: areas4714/4817, complete/rewarded14465 до reward24438. Это возвращает видимость Mia и устойчиво к relog. Остальные зоны и произвольные существующие rules не переписываются. Полёт/телепорт вместо лошади не используется. [Описание и исторические комментарии задания](https://www.wowhead.com/quest=14465/to-greymane-manor) подтверждают поездку с высадкой у основания поместья. Native fixtures проверяют last point, чужого пассажира, early dismount, COMPLETE, cleanup и фазовый predicate. Геометрия26972, открытие ворот и полнота сцены требуют клиентской проверки.

Для летучей мыши24920 источник содержит60 точек полёта и14 возврата, но они не соответствуют сегментам текущего C++; механический перенос ID запрещён. Для Tobias24902 источник содержит лишь одну точку, для stagecoach24438 подходящих маршрутов нет. Они пока не считаются восстановленными.

### Постоянные поздние фазы

`2026_10_06_10`:186 заканчивается после reward24676;187 начинается после этой награды,190 после принятия24903,188 после принятия24678,189 после принятия24680. Последняя заканчивается после reward14434. Правила действуют только в известных Gilneas zones4714/4755; existing custom rules сохраняются. Границы основаны на действующих queststarter/ender и фазах persistent spawns; это адаптация под текущую БД, а не подтверждённый retail sniff. Никакой COMPLETE/reward/teleport не выдаётся новым SQL.

Lorna37783 остаётся в186 до сдачи24676. Два конкретных спавна Lorna37783 и Krennan38553 используют native PhaseGroup440 (186+187), чтобы не потерять questgiver/контроллер армии после перехода. PhaseId0 при ненулевом PhaseGroup440 **не** означает снятие фаз. Источник, SHA DB2 и точные masks записаны в `docs/audit-data/gilneas-late-phases-source.json`. Native predicate tests проверяют accept/complete/reward, отказ от24678, сохранённые состояния после relog и постороннюю зону. ClientDB2 доступен26654: поддержку group440 и видимость всей последовательности необходимо подтвердить на26972.

Проверка свежего опубликованного world дампа00–09 на MySQL8.0.45 PASS; поздний10 проверяется отдельно. GCC полного6fcd532 PASS, Reliabilitya88c829 PASS. Эти результаты не подменяют проверку новых09–10.

### Leader of the Pack14386

`2026_10_06_11`: bindings36409/36405 и additive check68682. Нативный effect68682 уже summons36409; дополнительного summon/linked-spell нет. Три существующих Thyala и23 постоянных мастифа уже в182 — спавны не удаляются, quest ID14386 не используется как creature credit. Исправляется только известное ошибочное KillCredit1=14386, если такой legacy workaround присутствует.

Контроллер принимает участника активного14386, выбирает живую Тиалу в той же фазе, не перехватывает чужой tapped target. SummonList заменяет underflow-подверженный счётчик. Лимит50 проверяется перед каждым summon; death+despawn не освобождают два места. После отмены/смерти/выхода/потери цели/фазы/удаления родителя псы очищаются;120s ограничивает контроллер, дочерние actor lifetime30–60s сохранены. Reset контроллера очищает детей и восстанавливает ограниченный таймер, сохраняя owner. Постоянные мастифы без owner сохраняют обычный combat.

У generic NPC summons один OwnerGUID **не** выставляет IsControlledByPlayer, а `Creature::SetLootRecipient(NPC)` отклоняет NPC. Поэтому scoped DamageDealt связывает **реальный ненулевой урон** принадлежащего участнику пса по назначенной Тиале с player loot recipient и player damage requirement. Учтён native health multiplier; уже player-controlled damage повторно не учитывается. Это позволяет штатному Unit::Kill/RewardPlayerAndGroupAtKill выдать зачёт реального убийства. Scripted KilledMonsterCredit при простом наблюдении смерти удалён. Другие цели/владельцы/фазы/задания не меняются; quest автоматически не завершается.

Native fixture проверяет50/60 triggers, death+despawn, свободное место, назначенный target, живого owner, scaled damage, zero damage, чужой tap, отсутствие double-count, ordinary static AI, cancel/death/logout/timeout. Полный engine kill и клиентская сцена остаются приёмкой. [Leader of the Pack](https://www.wowhead.com/quest=14386/leader-of-the-pack) и native item49240→68682 подтверждают использование стаи; старый SQL с удалением всех псов/quest-ID credit не импортирован.

### Slowing the Inevitable24920

`2026_10_06_12`: исправлены432 конкретных релизных спавна (38615,51 уничтожитель38287,380 захватчиков38363) с188 на190, соответствующую questgiver38539 и новым постоянным правилам. Обе цели используются только24920, другие creature entries и пользовательские GUID не меняются. Существующий NPC38615 получает spellclick;72472 cast_flags0→1 вызывает нативный SUMMON38540 от игрока. DB2 SummonProperties161 имеет category VEHICLE; штатный EffectSummonType сам выполняет ride. Additional CheckCast запрещает inactive/dead/чужую карту/второй транспорт/отсутствующий nearby38615; summon effect не подменяется.

60 реальных точек полного круга и14 возврата из закреплённого DarkSite world перенесены только как coordinates. Предыдущая трёхсегментная схема не имела маршрутов; новый AI согласован с фактическими60/14 endpoints. Это один ограниченный полный круг с высадкой, не выдуманный endless loop. Manual return72849 теперь изменяет state и возвращает по реальному маршруту; прежний hook только менял path без state, поэтому landing не выполнялся. Timeout120s тоже возвращает по маршруту, cancel возвращает живого пассажира. Death/logout/early dismount очищают vehicle; неудачная посадка ограничена10s.

Обработка допускает только owner/seat0, игнорирует повторную посадку владельца и чужую высадку. COMPLETE после бомбардировки не выбрасывает игрока из воздуха: остаётся доступен штатный return button. Landing только на endpoint60 или14 нужного state, без телепорта/credit/autocomplete. Native bomb72247, VehicleID641, damage, cooldown и objectives6+40 сохранены. Provenance,74 точки и полный список432 actor GUID в `docs/audit-data/gilneas-bat-source.json`. Native fixture — circuit/return/button/duplicate/endpoint/owner/complete/abandon/death/logout/failed boarding. Проверка дальности/урона бомб, реального пролёта26972 и количества достижимых целей требует клиента.

Дополнительно: AI factory36405 отдаёт persistent мастифов обычному selectAI; новый questAI используется только TempSummon. Пользовательский AIName этого шаблона не очищается. Для horse36741 duplicate boarding владельца теперь не вызывает принудительное спешивание.

CI наa88c829: GCC и Windows полные сборки PASS, Reliability PASS, MySQL gilneas-chain PASS. На5baa187 Reliability с ASan/UBSan PASS, полные сборки выполняются. Это не результаты ещё не опубликованного12.

Пакет00–12 локально: native mechanics/vehicles/pack/phases PASS; MySQL8.0.45 первичное/повторное применение,74 bat/28 horse points,432 actor phases, route conflicts, чужие scripts/tables/Draenor rules PASS. Binding snapshot:94 зарегистрированных класса,77 BOUND,17 MISSING_BINDING; диагностика копии без повторного раннего05.10_04. Это не17 оставшихся квестов: часть классов связана с другими стадиями или небезопасными неподготовленными сценами.

### Проверка сборок и приватности временных NPC

На5baa187 полные GCC/Windows сборки обнаружили шесть неверных вызовов InSamePhase(Player*). Исправлены на InSamePhase(player->GetPhaseShift()); Также исправлены два аналогичных вызова в новом bat AI/hook; обе native fixtures теперь используют реальную сигнатуру PhaseShift const&, чтобы не скрывать такую несовместимость. Reliability и полный MySQL workflow на5baa187 PASS.

TempSummon дублировал флаг приватности WorldObject: Map записывал производное поле, CanSeeOrDetect читал базовое. Удалено дублирование, используется единый штатный флаг WorldObject. Native fixture воспроизводит ошибку на старом header и проходит на исправленном; проверяет owner/другого игрока, переключение через оба типа указателей, публичных NPC и приватные GO. Флаг по умолчанию остаётся false. Полная сборка и клиентская проверка персональных сцен ещё требуются.

### Exodus24438: предыдущий этап аудита маршрута

В закреплённом Pandaria source найден реальный маршрут4492801 из33 точек. Проверка actual Detour на предоставленных mmaps654 загрузила51 tile: все33 точки имеют ground polygon, все32 соседних сегмента дают полный путь без partial/buffer overflow. Это подтверждает проходимость предоставленной геометрии, но не retail timing/анимации/VehicleSeat клиента26972. Proof и координаты: `docs/audit-data/gilneas-stagecoach-route-audit.json`.

Текущий код ждёт28/33/44 вместо исходных24/30/33. Отсутствует carriage в seat2 harness; Marie занимает player seat1 вместо source seat0. Посадка зависит от порядка IsSummonedBy/JustSummoned, нет надёжного owner/duplicate/timeout cleanup. Старый source cast_flags0 нельзя копировать: Unit::HandleSpellClick этого ядра требует caster-clicker flag1 для посадки accessory на parent. Нужны адаптированный ограниченный FSM, guarded SQL и fixture; этот аудит НЕ активирует сцену и не меняет спавны.

### Exodus24438: код, аксессуары и маршрутизация

`2026_10_06_13` добавляет проверенный33-point path4492801, bindings44928/43336/43337 и недостающие car accessories в seat2 persistent38755/dynamic43336. Marie в static/dynamic car переносится с player seat1 в подтверждённый NPC seat0. Native Vehicle959 использует VehicleSeat9568 для seat1; harness958 имеет8197 в seat2, persistent970 использует его copy8233. Данные DB2/их SHA и26654 ограничение сохранены в route audit.

Accessory spellclick46598 cast_flags1 садит accessory на parent; старый72767 у static harness/car удаляется только в известном варианте0/0, поскольку он SUMMON43336 и непригоден для установки аксессуаров. Старые summon type0 исправляются на native manual8/minion1 только для проверенной композиции этих четырёх транспортов. Чужие route coordinates/seat occupants/bindings/click handlers вызывают отказ ДО permanent writes; неизвестные шаблоны/VehicleId тоже отклоняются. Другие world spawns, задания, обычный combat и terrain phases не переписываются.

Gossip и native right-click parked vehicle ведут в одну private owner-only поездку. Vehicle::Install автоматически добавляет SPELLCLICK при свободном player seat: поэтому static AI после native boarding сначала высаживает игрока из parked car, затем запускает private harness. Это исключает бесконечную посадку в неподвижную карету. Неучастники/повторный старт/чужой owner/неверное место не допускаются. Summon(Position) передаёт vehicleId0 и private=true отдельно, TTL450s; failed summon снимает только temporary phase194.

Посадка работает при обоих порядках IsSummonedBy/JustSummoned и отложенном native accessory join. Ride72764 сохранён; explicit basepoint2 выбирает seat1, а не seat0 Marie. Один native MovePath начинается через3s после посадки. Реплика Lorna наpoint24, реальная высадка/снятие194 на30, drive-away cleanup на33. Нет teleport/credit/CompleteQuest/reward. COMPLETE здесь — штатное состояние принятого задания без objectives, не scripted autocomplete.

Early dismount/cancel/death/logout/map/phase loss/reset/car loss/450s timeout очищают parent, horses, carriage и её passengers; failed boarding ограничен10s. После плановой высадки разрешена сдача задания до конца drive-away. Cleanup не выбрасывает игрока из постороннего транспорта. OnLogin удаляет orphan194 после restart/relog, обычные story phases/quest state сохраняются; OnLogout очищает текущий собственный vehicle.

Native fixture проверяет обе callback очередности, delayed join, parked click/gossip, seat conflicts, duplicate boarding, два владельца, endpoints/motion type, planned/early dismount, reward after landing, death/cancel/logout/restart/reset/lost carriage/timeout. Реальная посадка/анимации/звук Lorna/появление static car/высадка26972 ещё требуют клиента. Source не является retail sniff: timing3s сохраняет прежний script, endpoints24/30/33 взяты из закреплённого Pandaria implementation.

CI наfb4056b: GCC/Windows/Reliability PASS; MySQL gilneas-chain наde17960 PASS с теми же SQL00–12. Это результаты предыдущего пакета, не проверки нового13.

Наpoint30 высадка находится в4.291m от действующего questender37065/GUID802021. Его phase186 доступна после reward14467, ещё до принятия24438; existing persistent rule сохраняется до24676. Не добавляется искусственная фаза ради сдачи. Проверка shared visibility/анимации parked spellclick и надёжности высадки всё ещё входит в клиентскую приёмку.

Пакет00–13 на чистом импорте опубликованного20260926 world архива: MySQL8.0.45 PASS; отдельный disposable schema удалён после проверки. Повторное применение,33/28/74 route coordinates,432 bat phases,vehicle accessories/seat1/click flags,foreign conflicts/custom scripts и все посторонние таблицы проверены. Один предшествующий прогон остановился на bat actor assertion без указания строки; повторная проверка всех432 exact rows и полный новый импорт PASS. Диагностика теперь содержит GUID/entry/result/фактическую строку. Причина первой остановки не установлена; ошибка не объявляется исправленной без воспроизведения. Проверяемые SQL SHA и ограничения: `docs/audit-data/gilneas-chain-mysql-validation.json`.

Binding snapshot после00–13: 94 классов, 94 BOUND, 0 MISSING_BINDING. Это диагностика привязок, а не количество незавершённых заданий. Reliability16c5424 и62ecc17 с ASan/UBSan PASS, включая protection of harness accessory seats. GCC/Windows62ecc17 PASS; MySQL gilneas-chain16c5424 PASS, полный SQL workflow ещё выполняется.

Свежий релизный dump даёт94 BOUND, в отличие от ранее проверенной локальной копии. Привязка может присутствовать в creature override, а не только в creature_template. Сам статус BOUND не подтверждает существование маршрута, безопасный FSM или работоспособность задания; escort24902 и story scenes остаются отдельной работой.


## Годфри24592: безопасность окончания движения (SQL14)

В текущей БД Godfrey37875/GUID802361 и Genn37876/GUID802362 стоят в map654/phase186. Маршрут802361 отсутствует; Godfrey creature_text group0 также отсутствует. Старый Genn запускал MovePath на Godfrey, отключал ему гравитацию, но ожидал MovementInform(point4) на себе. Таким образом, окончание реального движения не могло закрыть сцену. Ошибка повторяется в закреплённых ArkCORE-NG a7304c3 и Ashamane b09c1c3; эти реализации не считаются готовым исправлением и не импортированы.

Собственный CreatureScript Godfrey принимает окончание WAYPOINT_MOTION_TYPE/point4, проверяет существование и конечные координаты маршрута перед стартом и не переключает гравитацию вручную. Общий актёр резервируется одним Genn; повторная сдача не перезапускает движение. Reset/death/исчезновение контроллера/map/phase loss/60s timeout освобождают сцену. При отсутствии пути NPC остаётся на месте, лог сообщает об отсутствии данных один раз за экземпляр AI; не выдаётся искусственный credit и не вызывается despawn. Существующая реплика Genn, реакция игрока и снятие stealth сохраняются; отсутствующий текст Godfrey не выдумывается.

SQL14 привязывает только пустой/наш ScriptName при пустом AIName. Другие custom AI, временные Godfrey и NPC вне map654 сохраняют обычную фабрику. Native fixture компилирует оба production класса и реальные WaypointNode/WaypointPath definitions: callbacks, route validation, reservation, reset, death, phase loss, timeout и отсутствие ScriptId проверены. Тестовый маршрут в fixture служит только для проверки алгоритма и не является маршрутом игрового мира. Проверки SQL включают повторное применение и сохранение custom ScriptName/SmartAI.

Сцена24592 пока НЕ завершена: нужен подтверждённый маршрут прыжка/падения, текст Godfrey и проверка визуального результата в клиенте26972. Четыре крупных незавершённых участка остаются:24902 Tobias,24904 battle,14401 Grandma,24592 Godfrey;14400/24627 требуют клиентской диагностики. Рабочий сервер этим пакетом не обновляется.

Источники: [ArkCORE-NG](https://github.com/Arkania/ArkCORE-NG/blob/a7304c3075bf8ee7eb5bdf45f31cda01c8626b52/src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp), [AshamaneCore](https://github.com/AshamaneProject/AshamaneCore/blob/b09c1c393cf2e01bc5e857ea6117680d2aaeadb0/src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp). Локальные данные и ограничения: `docs/audit-data/gilneas-godfrey-departure-audit.json`.

Проверки4b93abb: local MySQL8.0.45 isolated clone SQL00–14 PASS (schema удалён); native Godfrey/rescue fixtures PASS; Reliability37428861065 с ASan/UBSan PASS. GCC37428868338, Windows37428872089, release SQL37428864565 и local fresh full release test пока выполняются. Предыдущий fresh-release proof00–13 сохраняется без переименования в проверку14.


## Двое у моря14382: катапульты (SQL15)

В релизной копии36283/Vehicle516 имеет пустой ScriptName, seven persistent spawns phase182, native control spell68659, click69434 с cast_flags0 (ошибочный caster) и machinist36292/accessory seat2 с несуществующим enum summontype0. Клиентские Vehicle/VehicleSeat layouts совместимы с ядром: control seat0/5887, launch seat1/5888, machinist seat2/5889(copy5847). Это данные26654; проверка полного клиента26972 остаётся обязательной.

Прежний code делал оператора неуязвимым, освобождал катапульту при выходе живого механиста, пытался восстановить его в player seat0, терял EventMap при reset и телепортировал игрока к первому произвольному NPC. Обычный CreatureAI::OnCharmed также отключает AI при player control, поэтому обработка launch могла прекращаться. Привязка сама по себе этих ошибок не исправляет.

Новый AI сохраняется при управлении. Native accessory остаётся вseat2; при приближении участника задания механист выходит и вступает в обычный бой. Катапульта доступна только после его смерти, для живого участника14382 (INCOMPLETE либо COMPLETE до сдачи), controlseat0. Boarding без кнопки не запускает игрока. Launch68659 принимает штатную trajectory destination и скорости, проверяет координаты/native max range и блокирует повторный запуск. Через2s применяется native safe-fall66251, игрок выходит из собственного vehicle и выполняет MoveJump в выбранную точку; никакого NearTeleportTo, nearest-NPC target, fake credit/CompleteQuest. Cancel/death/logout/map/phase loss/reset/early exit очищают pending launch; другие игроки не сбрасывают owner.

Native96114 пересаживает player0→1. Кресло1 требует eject arc, которого Unit::_ExitVehicle в этом ядре не реализует. Поэтому forcecast96114 подавляется только в68659, игрок остаётся вcontrolseat0 до launch spline. Это явно ограниченная реализация движения, не заявление о точном воспроизведении retail seat animation. 2s сохраняет прежний timing, который ещё нуждается в клиентской проверке. Native fiery boulder68591 сохраняется, пока живой оператор находится в катапульте. Reset operator через3min не трогает занятый транспорт и возвращает native machinist вseat2; живой оператор не дублируется. Сам механист не получает scripted immunity.

SQL15 исправляет только binding36283,69434 caster flag1 и native accessory summontype7/minion0. Foreign VehicleId, control spell, custom AI, seats/minions/accessories/click handlers приводят к ошибке ДО permanent writes. Собственные hooks/spawns/капитаны/цели задания/phase rules и другие игровые системы не переписываются. Fixture компилирует actual production AI+SpellScript с API doubles; проверяет manual button, operator death gate, seat0 ownership, same destination/speeds, duplicate/reset/cancel/death/logout/phase loss, range/NaN/invalid velocity и operator seat2 rearm. Доказательства: `docs/audit-data/gilneas-catapult-audit.json`.

Предыдущий пакет4b93abb: GCC PASS, Reliability с ASan/UBSan PASS, MySQL gilneas-chain PASS; local fresh release SQL00–14 PASS, disposable schema удалён. Windows PASS. Эти результаты не объявляются сборкой нового кода катапульты. Для14382 нужна приёмка: убить механиста, manual launch на оба корабля, miss/early exit, безопасное приземление, обычное убийство36397/36399 и native objectives без добавленного credit.

Катапульты: native production fixture PASS; полный SQL00–15 на isolated local clone MySQL8.0.45 PASS, schema85e01b4599 удалён. Повторный импорт и guarded conflicts проверены. Full GCC/Windows/sanitizer/release SQL CI запускаются на новом code commit; клиентская приёмка ещё нужна.

CI катапульт ff60e37: Reliability37432693173 (ASan/UBSan) PASS. GCC37432702210, Windows37432706407 и release SQL37432697788 ещё выполняются. Клиент26972 не проверен; работа на production не выполнялась.


## Бабушкин кот14401: персональная сценка (SQL16)

Подтверждён маршрут Grandma из закреплённого Pandaria5.4.8 e0a20613: spawn(-2098.366,2352.075,7.160643),4 точки подхода/возвращения. Actual Detour на предоставленных mmaps654 загрузил51 tile:5 ground points,4 complete segments, без partial path/overflow. Человеческая Display30288 и Worgen36852 присутствуют в CreatureDisplayInfo26654, layout0x406268DF соответствует ядру. Source coordinates сохраняются; nav_z отличается до1.123m вследствие предоставленной rasterized geometry, это не замена VMAP/client testing. Proof: `docs/audit-data/gilneas-grandma-scene-audit.json`.

Chance создаёт owner-only Lucius сTTL180s. Он подходит к коту, произносит existing group0 (старый group1 отсутствовал), наклоняется и начинает обычный бой после catch. На4s catch+1.5s создаётся personal Grandma: human подход по двум точкам, transform36852/existing text0, attack delay800ms. После смерти Lucius helper ждёт4s, проходит исходные две return points и despawn. Shared Chance не удаляется, persistent questgiver Grandma не меняет флаги/модель/место/доступность сдачи; GetAI отдаёт их, public summons и foreign maps обычной фабрике. Temporary questgiver/gossip flags убираются только у helper. Native personal visibility выставляется до AddToMap/AI initialization и InitSummon, поэтому оба actor factory используют тот же inherited flag, ранее проверенный summon-visibility fixture.

Lucius выполняет source shoot41440 на расстоянии>2m и обычный melee, его combat movement отключён только на personal actor. AttackStart обоих актёров разрешает лишь участников собственной сценки. Нет nearest Grandma cross-player callback, captured raw pointer events, generic NPC/passivity edits, artificial credit или autocomplete. Actual player/pet positive hit ставит native tap; helper damage разрешён лишь при штатном IsDamageEnoughForLootingAndReward и owner loot recipient. Это сохраняет нормальную добычу49281 даже если Grandma наносит последний удар: не сбрасывается player damage requirement, не выдаётся item scriptом, не вводится 1% health floor. До необходимого реального урона игрока helper attacks остаются визуальными, без сокращения здоровья Lucius.

Quest abandon/death/logout/map/phase loss, evade/reset, missing actor/display и stalled180s lifecycle ограничены. GUID ownership сохраняется в delayed callbacks; two-player fixture проверяет, что чужой Lucius/helper никогда не запускает возврат/cleanup. DEAD Lucius сохраняет обычный lootable corpse. Loot COMPLETE позволяет helper закончить возвращение, а reward/отмена удаляет её. Source unsafe logical OR flags/shared nearest lookup/lambda captures не импортированы.

SQL16 только ставит ScriptName36458 при пустом AIName и blank/наш script. Existing faction/npcflags/unitflags/models, persistent spawns, creature_text/sound/locales и creature_loot_template не переписываются; custom AI сохраняются. Fixture компилирует production обаAI+Chance и actual native loot gate/LowerPlayerDamageReq, ownership/phases API doubles. Grandmother/horn tests PASS; full MySQL00–16 и новые CI ещё проверяются. Приёмка26972 нужна для approach/transform/taunt/shoot/return, двух одновременных игроков и loot cat при player/pet/helper final hit. Shared Chance hiding остаётся cosmetic review: unsupported per-player destroy packet или global despawn не добавлялись.

После подготовки этой сценки основные следующие участки кода:24902 Tobias,24904 Battle,24592 Godfrey. Это не заявление о завершении цепочки:14401 ещё требует клиентской приёмки,14400/24627 — диагностики в клиенте,14382 — flight/landing acceptance.

SQL00–16 MySQL8.0.45 isolated local clone PASS, schema после успеха удалён; native Grandma/horn fixtures PASS. Это не production обновление и не полная сборка нового кода.

CI7ab8c10: Reliability37435103225 с ASan/UBSan PASS. GCC37435110614, Windows37435114835 и release SQL37435106932 выполняются. Предыдущий катапультный GCCff60e37 PASS, MySQL gilneas-chain PASS, Windowsff60e37 пока выполняется. Рабочий сервер не обновлялся.


### Battle for Gilneas (24904): target lifetime and idle state

The six battle leaders in `zone_gilneas_city2.cpp` now clear their target list before each grid scan. Native `Unit::GetAttackableUnitListInRange` appends to the supplied list; retaining it between scans accumulated duplicates and could dereference units already removed from the map. Each scan now uses only its current grid results. Wave, point, distance, target and completion flags have defined initial values before periodic watchdogs execute. Routes, attack ranges, damage rules and quest credits are unchanged; no SQL is required.

`contrib/tests/test_gilneas_battle.py` compiles all six actual production `FindTargets` bodies and their state declarations. It tests repeated scans, destruction of a previous target, an empty grid and the existing special enemy spacing. Local Windows strict-warning compilation and execution passed. Linux ASan/UBSan and full Windows/GCC builds are submitted through CI; their results must be checked separately. Entity/grid behavior is a fixture, not a client playthrough.

Quest 24904 is **not yet declared restored**: replay/stale gossip validation, shared scene participation, controller reset, wave synchronization and the final cinematic still need audit and client acceptance. Tobias 24902 and Godfrey 24592 remain substantial scene work; 14400/24627 need client diagnosis. No running server was updated.


### Battle for Gilneas (24904): validated, idempotent scene start

Krennan now uses the same eligibility check for displaying and accepting the start option. Selection rechecks the living player, map 654, phase, native interaction distance, incomplete quest, living controller with its expected script and a registered living Liam nearby. A merely nearby, unregistered prince cannot trigger the event during initialization. The sender must be the normal gossip sender. Only a successful start emits Krennan's invitation line.

Krennan reserves the start before notifying Almyra, and Almyra independently ignores duplicate start actions. Her active state also blocks a fresh Krennan menu after Krennan resets while the existing controller is still running. This preserves the shared public event; it does not create private armies or change quest credits, routes or combat. The controller's reservation lasts for its existing lifecycle and despawn; general reset and interrupted-scene recovery remain pending audit.

`test_gilneas_battle_start.py` compiles production gossip selection, eligibility/start methods, Krennan action handling and Almyra's actual start case/GetData. Local strict-warning compilation and execution passed for two players with stale menus, direct duplicate callbacks, wrong sender, cancel option, cancelled quest, death, map/phase/range changes, missing or unregistered actors and a foreign controller script. New CI is submitted, not yet confirmed. Previous commit `fcd87fb` passed full GCC, Windows x64 and Reliability ASan/UBSan CI (37439473885, 37439478411, 37439520747).

This is a start-safety correction, not full client acceptance of quest 24904. Wave synchronization, scene recovery and the final cinematic still need work. No SQL or production-server changes were made.


### Battle for Gilneas: full-build correction and bounded wave callbacks

Commit `c22cc99` passed Reliability ASan/UBSan (37442953011), but full GCC (37442956940) and Windows (37442961423) failed because `ObjectMgr.h` was missing for the new `sObjectMgr` lookup. This include is now explicit. The prior fixtures mocked ObjectMgr and did not verify that production include; the new route test also checks the include/native declaration. Full builds remain the authoritative compatibility check.

All six battle leaders now ignore wave movement notifications belonging to another wave or a finished route. King Genn's separate point 1002 cinematic callback remains unchanged. A queued fight event after the final point hands off via the existing move event rather than indexing the route again; idle fight events are ignored. Every one of the 31 route lookups checks its actual native array size. Invalid lookups return the actor's current position rather than map origin, without teleporting or changing any original route coordinates.

The existing ten-minute reset protocol is now broadcast when the opening event starts, not only after the first wave finishes. This covers a stalled opening speech; normal wave transitions still refresh the same timer. This does not implement participant-specific abandonment recovery or guarantee simultaneous respawn of all persistent actors; those require further audit and client testing.

`test_gilneas_battle_waves.py` compiles the actual 27 coordinate arrays, six lookup methods, six movement callbacks and the six fight-entry guard prefixes. It checks all valid points in 31 lookup branches, endpoint/maximum indices, idle and stale callbacks, valid fight entry and the separate king cinematic callback. Grid, motion and EventMap scheduling are fixtures; the rest of each combat handler is not executed by this test. Local strict-warning builds/execution of wave, start and target tests passed. New ASan/UBSan and full builds are submitted separately; no new success is claimed yet. No SQL or running-server update was needed.


### Battle for Gilneas: independent leader arrival and current player presence

Almyra's `ACTION_DARIUS_ARRIVED` previously fell through to `ACTION_GENN_ARRIVED`; Darius could therefore mark the king arrived before the king actually reached his route endpoint. The missing break is restored. The native readiness masks for waves 1–7 are unchanged, but readiness now has an explicit false result for unknown/idle waves rather than reading an uninitialized mask. The player-presence bit is refreshed on each readiness check, including clearing it when no player is nearby; waves 3–7 no longer accept a presence recorded earlier after that player has left. Waves 1–2 retain their existing leader-only gate. The definition of `IsPlayerNear`, routes, combat and quest credits are unchanged.

`test_gilneas_battle_sync.py` compiles the actual arrival switch cases and readiness method. Local strict-warning compilation/execution passed for independent and duplicate Darius/Genn notifications, every required leader in every wave, player departure/return and invalid wave values. Entity proximity is supplied by a fixture, not a client playthrough. CI for prior `7e782c9`: Reliability 37447862028 succeeded; full GCC 37447865979 and Windows 37447870257 were still running when this work started. New full builds and sanitizers are submitted separately. Shared event abandonment/recovery and the final cinematic still require further audit; quest 24904 is not declared fully restored. No SQL or running-server changes were made.


### Battle for Gilneas: finale callback identity and idempotence

Sylvanas starts the final cinematic once, queues Liam's death response once only after the cinematic starts, and dispatches the existing nearby incomplete-quest spell/credit and departure once. The original seven-second delay, 50-yard credit radius, spell and objective remain unchanged. Liam accepts the death shot only from his registered Sylvanas GUID in the same phase, and reacts once; duplicate or foreign-scene shots no longer repeat the king's movement/dialogue. These flags belong to each AI instance and remain latched throughout the scene, including incidental Reset calls.

Sylvanas previously scheduled EVENT_GLOBAL_RESET but had no corresponding handler. It now clears queued events, removes its followers and despawns after the existing delay. This does not yet guarantee cleanup of every other shared actor or recovery of missing scene routes.

`test_gilneas_battle_finale.py` compiles actual start/death/completion/reset switch cases and Liam's full SpellHit method. Local strict-warning execution passed for premature completion, duplicate actions/shots, a foreign Sylvanas, phase mismatch, single native credit dispatch, preservation of already-complete quests, single king reaction and timeout cleanup. Entity/quest credit and EventMap scheduling are fixtures; this is not a live server or client scene test. Previous 6ee5823 Reliability ASan/UBSan 37449769523 succeeded; GCC 37449773667 and Windows 37449778145 were still running when work began. New full builds are required. No SQL or production-server update was performed. Full quest 24904 acceptance, shared actor recovery and the rest of the Gilneas chain remain pending.


### Battle for Gilneas: king timeout and stop processing after teardown

Genn 38470 had an ACTION_EVENT_RESET_TIMER handler that scheduled EVENT_GLOBAL_RESET, but UpdateAI never handled that event. Its reset handler now uses the same follower cleanup and delayed despawn as the other battle leaders. Almyra, battle Liam, Myriam, Lorna and Darius now reset their event queues and return immediately after timeout teardown, preventing another due movement/combat event in the same update. Together with the previous Sylvanas fix, all seven timeout handlers stop event processing. Krennan's existing reset remains unchanged. Original ten-minute timers and 100ms despawn delays are retained; no credits, routes, actor respawn settings or SQL were changed.

`test_gilneas_battle_reset.py` compiles all seven actual timeout case bodies and executes each with additional queued fights. Local strict-warning execution passed: queued work is cleared, cleanup/despawn executes once and no fight follows teardown. The queue and entity methods are fixtures; persistent actor respawn, full scene restart and client visibility still need testing. Prior ea86d3a Reliability 37451714365 succeeded; GCC 37451718077 and Windows 37451721735 were still running at the start of this work. New CI is submitted separately. This does not declare quest 24904 or the full Gilneas chain complete. Production server was not updated.


### Battle for Gilneas: individual rewards must not remove shared actors

Read-only queries against the local release database confirm Lorna 38611 ends quests 24904 and 24902 and starts 24902, 24903 and 24904. Her reward hook previously ignored quest/player identity and sent ACTION_QUEST_REWARDED to a nearby shared Almyra, which despawned registered battle leaders. A returning player handing in a completed quest could therefore remove actors from another player's current event.

The individual reward teardown hook is removed; native quest reward processing and the existing Tobias summon on accepting 24902 are retained. The public battle continues to use its existing refreshed ten-minute reset timer for shared cleanup. This deliberately retains actors until the shared lifecycle expires instead of clearing them immediately for one reward. It does not implement per-player battle instances or change phase SQL, quest credit, rewards or actor respawn settings.

`test_gilneas_battle_reward.py` compiles the full production Lorna script and exercises two players rewarding 24904/24902/24903 and an unrelated quest, plus acceptance of 24902. Local strict-warning execution passed; entity behavior is a fixture. Previous 7a9846c full GCC 37453109720, Windows 37453113594 and Reliability ASan/UBSan 37453105713 all succeeded. New full builds and sanitizers are submitted separately. Multiple-player scene behavior, restart after all actors respawn and full Gilneas chain acceptance still require client testing. No SQL or running-server update was performed.
