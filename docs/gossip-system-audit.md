# Аудит Gossip subsystem в 1KYCore

## Основание и область проверки

Ветка: `feature/npc-crowd-separation`. Перед работой выполнены fetch origin и upstream. Исходный HEAD: `c5d4583160bdc74ba33f8a8136997a751534412d`; он совпадал с origin. SylvaniaCore: `30bfb3cf13520bf032737d3e5c607e57d547f128`, ветка upstream/sylvaniacore. Другие ветки не изменялись.

Проверены handler, GossipMenu/PlayerMenu, Player::PrepareGossipMenu/SendPreparedGossip/OnGossipSelect, ScriptMgr, выбор AI, SmartAI events, загрузчик меню и trainer paths. Выполнен лексический проход всех `.cpp` и `.h` в src/server/scripts. Это перечень мест для проверки, а не доказательство корректности каждой ветви каждого NPC.

Данные: read-only копия релизной world-базы `ru_target`, 7 867 options, 9 934 menu rows, 51 255 SmartScript rows, 110 482 creature templates, 49 276 GO templates. Эта копия не является рабочим сервером и не подтверждает, какие обновления применены на нём. Точные ключи и все кандидаты находятся в [полном отчёте](audit-data/gossip-system-audit-2026-10-08.json.gz); [краткий JSON](audit-data/gossip-system-audit-summary-2026-10-08.json) содержит счётчики, SHA снимка и ключевые ссылки.

## Root cause — CONFIRMED_BUG

Исходный HandleGossipSelectOptionOpcode проверял наличие кнопки, вызывал AI и только затем читал Sender/OptionType. ClearMenus или пересборка меню в AI уничтожали старую кнопку либо заменяли её индекс. Legacy CreatureScript/GameObjectScript получал нули или действие следующего меню вместо выбранного. Это последовательное изменение состояния внутри одного handler, а не гонка потоков.

Исполняемый тест исходного handler падает с `callback read mutated sender/action`. После исправления тот же тест проходит для creature/GO и обычного/coded выбора. Это подтверждает дефект ядра; исчезновение всех наблюдаемых симптомов на игровом сервере ещё требует клиентского теста.

Отдельно воспроизведены две ошибки dispatch:

* `new DB menu handled old click`: после AI/C++ fallback Player::OnGossipSelect мог прочитать уже новую DB-кнопку, если меню сохранило ID и индекс.
* `handled GO selection dispatched twice`: true от GameObjectAI::GossipSelect/Code игнорировался, после чего вызывались следующие обработчики. Контракт виден также в существующих icecrown_citadel_teleportAI и gob_rocket_sling, возвращающих true после выполнения действия.

## Core fix — FIXED IN CORE

1. Sender/OptionType копируются до callback; четыре legacy paths используют scalar snapshot. AI по-прежнему получает GossipID/GossipIndex, legacy script — Sender/Action. Индекс не подменяется действием.
2. Добавлена ранняя проверка packet.GossipID against текущего MenuId. PlayerMenu::SendGossipMenu передаёт именно GetMenuId; ClientOption — ключ map. PrepareGossipMenu сохраняет DB MenuId, scripted helpers используют тот же sender, включая menuId0; прямых альтернативных GossipMessage отправок в scripts не найдено. Native Player::OnGossipSelect уже проверял ID, но раньше эта проверка происходила после AI/C++ действий.
3. GossipMenu имеет серверный revision, изменяемый при clear, add/overwrite item, item-data или смене MenuId. DB fallback разрешён только для того же revision и SourceGuid. Он не применяет старый click к новому меню с совпавшими ID/index. Порядок AI → legacy script → native fallback сохранён.
4. true от GO AI прекращает последующий dispatch; false сохраняет legacy/native пути. CreatureAI sGossipSelect возвращает void и не получил современный bool API. Его совместное выполнение с CreatureScript само по себе не считается ошибкой.
5. DEBUG `network`: player/source, packet/current MenuId, index, sender/action, AIName/ScriptName; причины missing item, stale menu, source mismatch, unsupported target, невозможность взаимодействия, script reload и подавленный fallback. PromotionCode не выводится.

Изменены только NPCHandler.cpp и GossipDef.h/.cpp. Packet layout, SmartAI enum/API и скрипты квестов не изменены. Глобального ClearMenus перед кликом нет. SendCloseGossip и сохранение pending PlayerChoiceId не менялись.

## Upstream comparison

[Ashamane commit b09c1c393cf2e01bc5e857ea6117680d2aaeadb0](https://github.com/AshamaneProject/AshamaneCore/commit/b09c1c393cf2e01bc5e857ea6117680d2aaeadb0) возвращал legacy callbacks и сохранял sender/action перед AI. [Issue271](https://github.com/AshamaneProject/AshamaneCore/issues/271) относится к обновлению 9.x; последующий комментарий сообщает о неполном исправлении coded gossip. Это историческое подтверждение разделения идентификаторов, а не доказательство тождественности всех причин в Legion.

На проверенном [SylvaniaCore HEAD](https://github.com/BlaMacfly/SylvaniaCore/commit/30bfb3cf13520bf032737d3e5c607e57d547f128) присутствует прежний порядок post-AI getters. Логика сохранения PlayerChoice при закрытии уже имеется и в upstream, и у нас. Современный Trinity handler целиком не переносился.

## Lifecycle, lifetime и индексы

* ScriptMgr::OnGossipHello очищает меню перед существующим CreatureScript; при fallback PrepareGossipMenu снова очищает оба списка и выставляет MenuId. Отсутствие Clear в каждом OnGossipHello не является автоматически багом.
* ClearMenu очищает item и item-data, но оставляет MenuId. Это совместимо с nested/scripted menus; revision отличает пересборки с тем же ID. ClearMenus не должен глобально сбрасывать PlayerChoice.
* SendGossipMenu сбрасывает InteractionData и сохраняет SourceGuid; SendCloseGossip сбрасывает SourceGuid, сохраняя PlayerChoiceId. После server close выбор не проходит source check.
* В scripts не найдено прямых чтений GetGossipOptionSender/Action после Clear. Например npc_prof_alchemist очищает меню и использует уже переданные scalar sender/action — VALID. Повторение action под разными sender или в условных ветвях не доказывает collision.
* Из указателей на _menuItems найдены handler item и Player::OnGossipSelect item. Handler не разыменовывает item после callback. В native Player::OnGossipSelect type/cost прочитаны заранее; ActionMenuId используется до PrepareGossipMenu, после пересборки старый pointer не читается. Новая защита не даёт войти туда с меню следующего состояния.
* AddMenuItem(-1) корректно занимает первый свободный индекс: 0,2 →1; после clear возвращает0. ClientOption сохраняет этот ключ. Алгоритм не изменён.
* **REVIEW_REQUIRED / minor:** ASSERT(size <=32) перед вставкой допускает 33-ю строку, а explicit overwrite на полной map имеет другую семантику. Это отдельно от click defect; лимит и алгоритм не менялись без проверки клиентской необходимости и совместимого поведения при переполнении.

## Database findings — FIXED IN DATA: none

| Проверка | Результат в локальной релизной копии | Оценка |
|---|---|---|
| ActionMenuId без gossip_menu | 14 ссылок | 1 подтверждённая отсутствующая обычная destination; 11 имеют options и требуют проверки title; 2 FALSE_POSITIVE для native перехода |
| Unsupported OptionType | 3 строки с27: (19958,2), (19955,0), (18745,0) | CONFIRMED_DATA_ERROR: artifact refund type отсутствует в native enum/switch; MAX=30 сам по себе не ловит holes21–28 |
| Missing POI | 0 | В снимке не найдено |
| Trainer dependencies | 428 кандидатов: 127 VALID, 301 REVIEW_REQUIRED | Нет подтверждённого ненулевого TrainerId, отсутствующего в trainer |
| Smart binding без DB menu/index | 116 rows | REVIEW_REQUIRED: dynamic/default/GUID/C++ menus могут быть легитимны |
| Missing entry-level Smart selection | 283 owner/option cases | REVIEW_REQUIRED, не доказательство отсутствия handler |
| Multiple Smart select events | 117 групп | REVIEW_REQUIRED: последовательные actions, event phase/chance могут быть намеренными |
| SmartAI + ScriptName | 914 NPC и9 GO | REVIEW_REQUIRED; среди NPC77 имеют entry-level Gossip events |
| Orphan auxiliary option rows | 57 | CONFIRMED_DATA_ERROR по отсутствующей паре MenuId/OptionIndex; тексты/строки не удалялись |
| Conditions | 1 отсутствующая option binding, 1 review menu reference, 36 условий конкретных Gossip Smart events | Не оценивались runtime quest/race/class/map/phase/aura/level/objective состояния |

Подтверждённый обычный переход: **Menu21295/Option0 →21296**, Lantresor dialogue; нет ни target menu title, ни options. Правильный destination не установлен, SQL repair не создавался. Ссылки **10662/0 →1048576** (BATTLEFIELD) и **20086/1 →21664** (NONE) не выполняются native GOSSIP case: нельзя объявлять их причиной неоткрывающегося nested menu. Остальные 11 ссылок и все exact keys перечислены в JSON.

Trainer0 в Gossip вызывает legacy SendTrainerListLegacy и использует npc_trainer, включая одноуровневый отрицательный reference join. creature_default_trainer используется другим путём — HandleTrainerListOpcode. Инструмент различает эти случаи; отсутствие нового trainer0 не является автоматически ошибкой. Даже наличие legacy rows не доказывает валидность spells для данного игрока.

SmartAI GetAI selection сначала пробует CreatureScript::GetAI и только потом AIName. Наличие обоих полей не означает, что две AI работают одновременно. Нельзя массово очищать AIName/ScriptName по этому списку. Условия15 привязаны к menu/index, условия22 — к entry/source_type и eventId+1; locale влияет на отображение и не менялась.

## Read-only tool

`contrib/tools/gossip_audit.py` выполняет только SHOW/SELECT, сначала проверяет таблицы/колонки. При несовместимой схеме выдаёт incomplete/REVIEW_REQUIRED. MAX и поддерживаемые OptionType, Smart events/actions и flags читаются из текущих исходников. Shared menu0 отчёт агрегирует вместо миллионов ложных «ошибочных кнопок». Полный отчёт содержит C++ path/line, menu lifecycle calls, return values, repeated expressions и оценку REVIEW_REQUIRED.

Пример для копии актуальной world-БД:

```powershell
python contrib/tools/gossip_audit.py --database world_copy --host 127.0.0.1 --port 3306 --user audit_reader --export-snapshot gossip-snapshot.json --output gossip-report.json
python contrib/tools/gossip_audit.py --snapshot gossip-snapshot.json --output gossip-report-repeat.json
```

Для авторизации используются настройки mysql client / MYSQL_PWD; пароль не передаётся утилите отдельным аргументом и не записывается в отчёт. Рекомендуется снимок или неподвижная копия: SHOW/SELECT не обеспечивают согласованный снимок меняющейся MyISAM-БД. Автоматического repair режима нет.

## Regression tests

`test_gossip_dispatch.py` компилирует **фактический полный handler**, native GossipMenu declaration/methods и SendCloseGossip. Покрыты clear/rebuild, исходный action1001 против следующего2002, обычный/coded NPC и GO, независимые AI и legacy identifiers, DB fallback/revision, Menu A→B stale click, menu0/nested IDs, source/index rejection, server close/PlayerChoice, GO true и два игрока у одного NPC. Три сценария отдельно падают на исходном handler и проходят на изменённом. Текстовые assertions не заменяют выполнение кода.

`test_gossip_audit.py` проверяет классификации, реальный enum, отсутствующую схему, legacy trainer0 против default trainer, orphan records, динамические меню, SmartAI ambiguity, неизменность входного snapshot и агрегирование menu0. Локально также прошли существующие Gilneas quests, Mardum invasion/bombardment и campaign object fixtures. У Windows GCC нет ASan/UBSan libraries: локальные native tests выполнялись без sanitizers; Gilneas fixture запущена тем же способом через внешний runner без изменения её файла. CI запускает их с Linux sanitizers.

GCC, Windows x64 и Reliability regression должны быть проверены на опубликованном исправлении; до завершения CI этот пункт приёмки остаётся открытым. Результаты запусков публикуются отдельно, рабочий сервер не обновляется.

## Remaining unknowns — NEEDS CLIENT TEST

1. Нельзя отличить два **входящих** click packets с одинаковыми SourceGuid/MenuId/Index после закрытия/повторного открытия: в Legion selection нет nonce. Revision решает mutation внутри текущего dispatch, а не все replay случаи.
2. Клиентское закрытие окна без server close не всегда сообщается серверу; packet/current-menu/source validation не заменяет полного UI state tracking.
3. Coded route по-прежнему определяется непустым PromotionCode. Пустой ввод и внешние coded scripts требуют отдельной совместимой проверки; native SmartAI coded hook пустой. Строка кода не логируется.
4. Нельзя по локальной релизной копии гарантировать список ошибок рабочей БД, runtime flags, player phase/conditions или исправление всех intermittent symptoms. После core fix сначала повторить игровые тесты, затем разбирать оставшиеся воспроизводимые data/script cases.

## Client validation checklist — Legion 7.3.5

1. Открыть/закрыть одного NPC20 раз и выбрать ту же кнопку.
2. Быстро пройти A→B→C→назад и другую ветвь.
3. SmartAI NPC.
4. C++ CreatureScript NPC.
5. DB-only menu.
6. Trainer: новый trainer и legacy trainer.
7. Vendor.
8. Taxi, включая первое открытие нового узла.
9. GameObject, включая ICC teleporter.
10. Coded popup: верный, неверный и пустой ввод.
11. Gossip→PlayerChoice артефакта/class hall.
12. Gossip, меняющий quest state (Gilneas/Mardum/class halls).
13. Закрыть сразу после выбора и снова открыть.
14. Два игрока одновременно у одного NPC — независимые меню/действия.

Итоговые статусы: **FIXED IN CORE** — snapshots, stale MenuId validation, DB mutation fallback, GO handled contract; **FIXED IN DATA** — none; **NEEDS CLIENT TEST** — весь checklist и оставшиеся реальные NPC; **NOT A BUG** — сами по себе Clear в legacy OnSelect, trainer0, совпадающие actions под разными sender, menu0 и AIName+ScriptName.
