# Исправления Гилнеаса 11 октября 2026

- 14416: сдача лошадей и применение 68903 ограничены садом Краули (map 654, area 4807); вне сада выводится уведомление.
- 14401: бабуля Валь 801893 скрывается при взятии задания, 801903 видна во время выполнения и до сдачи. Видимость проверяется отдельно для каждого игрока.
- Люций 36461: два постоянных спавна удалены, личный призыв от кота сохраняется; уровень и диапазон масштабирования устанавливаются по игроку, характеристики пересчитываются.
- 36488: в Гилнеасе защитное поведение — отвечает на удар, самостоятельно не начинает бой.
- 36231: удалены 17 близко стоящих дублей, сохранены 9 распределённых целей и исходные характеристики задания. Спавны со связями, событиями или пользовательскими маршрутами сохраняются.
- 36671: добавлено отсутствующее масштабирование 5–20 без повышения уровня относительно игрока. Множители урона и здоровья не изменены.
- Реплики детей 14368 и Люция переведены по существующему английскому тексту. Это перевод, а не подтверждённые официальные цитаты; существующие пользовательские переводы сохраняются.
- 36512: 11 лис гуляют в радиусе 8 ярдов.
- Восстановлены 6993 пустых поля в 3067 строках локализации заданий из ранее проверенного пакета. Английский исходник должен совпадать, непустые переводы не заменяются. Аудит: localization/quest-dump-audit-2026-10-11.json. Это проверка доступного пакета, а не подтверждение полноты всех переводов игры.
- Пустое приветствие списка заданий для ruRU заменено на «Здравствуйте, имя.». Перевод стандартного BroadcastText 50429 уже есть в предоставленной hotfix-БД. Загрузка всех hotfix-локалей включена по умолчанию, чтобы английские DB2 не заменяли русские строки.

## Применение и проверка

Исходные дампы на рабочем столе и рабочий сервер не изменялись. Нужна новая сборка для C++ и стандартное применение world SQL-обновлений. В существующем worldserver.conf явно заданный `DB2.Hotfix.LoadAllLocales = 0` необходимо заменить на `1`; обновление .conf.dist не меняет действующий конфиг. Загрузка локалей может увеличить время запуска и потребление памяти.

На отдельной копии предоставленной базы проверены повторное применение, сохранение основных английских текстов, других таблиц и пользовательских настроек. Нативные тесты сценариев бабули и лошадей проходят. В клиенте ещё нужны проверки фаз двумя персонажами, уровня/урона Люция и разведчиц, сдачи лошадей, реплик детей и прогулок лис.

## Поездка «Исход» (24438)

Скорость бега личной упряжки 43336 увеличена на 60% относительно её текущего значения. Множитель применяется один раз при призыве; маршрут 4492802, диалоги и точки высадки сохранены.

28 спавнам следующей сцены 24472 (капитан Астер37806, Корот37808, катапульта37807 и солдаты37805, включая802093) добавлена отсутствующая аура80852. Удалений нет. Игрок обнаруживает их с84481, которую существующий скрипт Лиама выдаёт на время сцены. Сопоставление эффектов проверено по локальному SpellEffect.db2; данные и SHA256 в audit-data/gilneas-exodus-scene-visibility.json. GM может видеть скрытых NPC благодаря режиму GM.

Нативный тест повозки и проверки SQL на отдельной копии базы прошли. В клиенте нужно проверить новую скорость и появление/скрытие этой группы во время24472, затем её отсутствие во время поездки24438 обычным персонажем.

## «Застрявшие в болоте» (24468)

Вместо заполнения всех целей при одном разговоре каждый выживший37067 добавляет ровно1. Цель255768 переведена с крокодилов37078 на выживших37067, количество5 сохранено. Зачёт ограничен данным заданием; другие цели и боевой AI не меняются. Завершение выполняется только после штатной проверки CanCompleteQuest.

Список поговоривших игроков хранится отдельно в AI каждого NPC. Повторный разговор не даёт зачёт, второй игрок независим, изменение статуса задания очищает его отметки у загруженных выживших рядом. Стандартный счетчик прогресса сохраняется в character-БД; индивидуальные отметки NPC живут в памяти и могут сброситься при перезапуске/пересоздании NPC. Уже полученные по старому обработчику5/5 автоматически не откатываются.

Проверены пять разговоров1/5–5/5, повторный разговор, независимость игроков, сброс отметок для повторного прохождения, границы карты/фазы/расстояния и отсутствие полного зачёта до пятого NPC. SQL проверен на отдельной копии базы, включая повторное применение. Нужны новая сборка и SQL2026_10_11_07_world_gilneas_survivor_talk_credit.sql.

## Битва за Гилнеас (24904)

Шесть лидеров и сопровождающие используют бег с множителем 1,2. Координаты маршрутов, порядок волн, боевые способности и сценические задержки сохранены. Точка (-1613.41,1312.47,18.64) — конец третьей волны Лиама: дальнейшее движение зависит от прибытия остальных групп и присутствия живого участника. Проверка трёх маршрутов третьей волны по предоставленным MMAP подтвердила проходимость; данные в audit-data/gilneas-battle-march-audit.json.

Устранён риск пропуска поздних лидеров: перед стартом загружаются четыре известных сетки их спавнов, проверяются регистрация и готовность всех участников; поздние лидеры находят контроллер в пределах 700 ярдов вместо 100. Это исправление выявленной причины возможной остановки, а не подтверждение состояния AI на рабочем сервере. При очистке Лорны теперь удаляются старые GUID артиллеристов.

SQL 2026_10_11_08_world_gilneas_battle_actor_scaling.sql добавляет отсутствующее масштабирование 5–20 без прибавки уровня для десяти штатных участников, включая призываемого Горотa. Существующие настройки масштабирования сохраняются. Множители урона, здоровье боссов и способности не ослабляются: в предоставленном дампе обнаружено именно отсутствие масштабирования. Итоговую сложность боя нужно проверить обычным персонажем.

Смерть игрока не сбрасывает общий сценарий: этапы, требующие живого участника, ждут его возвращения. Действующий тайм-аут без прогресса около десяти минут сохраняется и позволяет начать событие заново. Нативные проверки охватывают смерть/возвращение, готовность лидеров, маршруты и повторное использование AI; SQL проверен на отдельной копии базы, включая повторное применение. Нужна проверка в клиенте: старт, прохождение остановки третьей волны, смерть и возвращение, финал и урон врагов. Рабочий сервер не изменялся.


## Полный аудит семи этапов24904 и восстановление реплик

SQL2026_10_11_09_world_gilneas_battle_dialogue.sql восстанавливает28 отсутствующих/штатных записей creature_text и привязывает их к существующим BroadcastText. Все28 английских и русских строк найдены в предоставленной hotfix-БД. Семь строк вступительной речи и другие подтверждённые голосовые реплики используют21 SoundKit, проверенных по локальному ruRU SoundKit.db2 и метаданным ядра. Пользовательские тексты, привязки, непустые переводы и другие локали сохраняются. Для локализованного BroadcastText нужен DB2.Hotfix.LoadAllLocales=1. Источники и контрольные суммы: audit-data/gilneas-battle-dialogue.json.

Финальные вызовы согласованы с группами Legion-дампа: Генн0 — приказ Лиаму,1 — «СИЛЬВАНА!!!»,2 — «ЛИАМ!!! НЕТ!!!»; Сильвана0 — остановка боя,1 — угроза,2 — уход после выстрела; сценический Лиам0 — «ОТЕЦ!!!»,1/2 — последние слова. Речь больше не должна заменяться молчаливым ожиданием отсутствующих записей. У девяти штатных строк дампа был общий ошибочный Sound19606; для точных исходных текстов он заменяется на подтверждённые привязки, остальные пользовательские Sound сохраняются.

|Этап|Участники и условие перехода|
|---|---|
|1: рынок|Алмира,Лиам,Мириам заканчивают собственные маршруты и локальный бой.|
|2: лестница|Те же три группы; переход только после их прибытия.|
|3: артиллерия|Добавляется Лорна; нужны четыре группы и живой участник рядом с Алмирой. Точка пользователя — конец пути Лиама этого этапа.|
|4: встреча с Дариусом|В контрольной точке17 Алмира вызывает Дариуса. Переход требует его прибытия и присутствия игрока. Есть отдельное ожидание участника в районе контрольной точки16.|
|5: Горот|Босс призывается перед началом этапа; отряды продолжают бой, пока рядом есть цель. При неудачном призыве переход повторяется без продления общего тайм-аута.|
|6: подход к Сильване|Пять групп завершают пути; Генн получает свою предбоевую реплику.|
|7: финал|Подключается Генн; контроллер в своей контрольной точке запускает45-секундный таймер завершения боя. Затем идут выстрел, гибель Лиама и зачёт игрокам с незавершённым заданием в50 ярдах от Сильваны. Восьмой волны нет.|

Важно: седьмой этап завершается собственным таймером сцены, а не обычным переходом в новую волну. Боевой Лиам уступает место сценическому призыву; его исчезновение здесь предусмотрено. Исправлена ошибочная отправка Генном уведомления о прибытии Лорны. Проверены31 назначение маршрутов для шести лидеров: размеры волн совпадают с массивами. Все27 различных массивов имеют найденную поверхность и полные внутренние пути на51 MMAP-тайле. Проверка Detour не заменяет прохождение живого боя, включая соединения между этапами, спутников и динамические препятствия.

У Лорны привязка артиллеристов теперь не смещается при исчезновении одного NPC; неполный призыв не блокирует движение оставшихся пушек и пехоты. Перед стартом проверяются финальные маршруты; новое SQL повторно восстанавливает их только при полном отсутствии, поскольку в свежем дампе их не было. Частичные пользовательские маршруты не смешиваются с исходными точками и требуют отдельного исправления.

Неудачный призыв сценического Лиама повторяется до пяти раз, массовые эффекты не повторяются. При устойчивой ошибке событие очищается существующим тайм-аутом, а не выдаёт незаслуженный зачёт. Ожидания волн3–6 возобновляются после возвращения живого участника. Финальная сцена использует собственные таймеры; смерть игрока не превращает их в бессрочное ожидание. Полная потеря отряда или отсутствие участника может потребовать повторного запуска после штатной очистки. Автоматически пропускать бой или телепортировать лидеров не стали.

Проверки: нативные переходы семи волн, фактические уведомления пяти лидеров, семь событий речи и время её завершения, обработка ошибок призыва, артиллерия при неполном составе, повторное использование AI, смерть/возвращение и финальный зачёт. SQL проверен на отдельной копии полного дампа, включая повторное применение, пользовательские тексты/локали и неполный пользовательский маршрут. Рабочая БД и сервер не менялись. После новой сборки и SQL нужен клиентский проход обычным персонажем через все этапы, отдельная смерть/возврат и проверка речи/голоса/финального зачёта.


## Follow-up: Manor dismount and invisible Exodus attackers

Quest 14465 now preserves its vehicle quest AI through rider charm. The inherited
CreatureAI::OnCharmed previously disabled it, preventing UpdateAI and endpoint
callbacks from running after boarding. Current-position manor checks and the
28-point endpoint remain in place; test both in the client with an ordinary player.

Apply 2026_10_11_10_world_gilneas_koroth_scene_passive.sql with the new binary.
The 28 audited persistent scene actors (GUID 802085–802112, matching entries
37805/37806/37807/37808) use passive AI and cannot initiate attacks. Other spawns
and summons retain default AI; custom ScriptName/SmartAI values are preserved.
Existing invisibility 80852 and scene detection 84481 remain unchanged. Verify
both Exodus 24438 and the later Koroth scene 24472, including movement/dialogue.
Invisibility is not phase separation and does not stop an invisible NPC from
seeing a visible player.

Ambusher 38762 now checks phase, visibility and valid hostility before throwing a
boulder. Legitimate visible attacks remain enabled. No blanket player immunity,
NPC damage nerf, or route/speed change is introduced by this follow-up. If damage
persists, capture the combat-log attacker and spell; that is needed to attribute
remaining attacks accurately. Production server and database were not updated.


## Quest 24592 duplicate targets

SQL 2026_10_11_11_world_gilneas_betrayal_duplicate_spawns.sql leaves Walden37733
GUID802443 (ground-floor random patrol) and Ashbury37735 GUID802419. Removes only
stock GUID802425,802426,802450,802416 at audited original coordinates in phase186.
Requires a surviving same-entry/map/phase actor and excludes custom waypoint,
formation, pool, event, linked-respawn and per-spawn SmartAI bindings. Quest
objectives265565/265566, templates, combat SmartAI and other phases are unchanged.
Native archived Walden252538 route begins at ground-floor Z77.740814, matching
retained actor height rather than the extra roof spawn Z86.8961. Client validation
of both targets in 24592 is still required. Apply SQL to world and restart or
reload affected grids; no binary change is required for this SQL-only follow-up.


## 2026-10-12: Krennan start menu and distant leader initialization

Live report confirms finale paths have 3/4 nodes, Krennan802514 uses PhaseGroup440,
and Liam802761 is at the restored start. Live creature_text query for38218/38553
returned no rows: apply 2026_10_11_09_world_gilneas_battle_dialogue.sql to the
actual world database, then reload creature_text and creature_text_locale or
restart worldserver. Stock result is Liam38218:14 lines; Krennan38553:1 line.
These are data repairs; a binary rebuild alone does not insert dialogue rows.

PrimeGilneasBattleActors now activates only the four audited late-wave spawn
instances after LoadGrid and native-script/map/phase validation. Map::Update visits
nearby cells of players and active nonplayers; grid loading alone does not make
remote inactive leader AI run EVENT_INITIALISE. Acknowledged leader initialization
retains existing15-minute active timers and battle reset behavior.

The Krennan menu distinguishes unavailable from already-running battles. An idle
scene always offers the native start action to a quest participant, even if a
leader is still initializing. Selection retries controller discovery and reports
which prerequisite is unavailable instead of silently closing. The existing
join-running-scene choice now reports that the army is already in the city; it
never restarts the shared event or grants credit/teleports. An ordinary-client
start, seven spoken motivation lines, subsequent march, late actors and finale
still require verification. Start/reservation remains guarded against duplicate
clicks, stale menus, wrong quest/map/phase and missing native actors/routes.


### Follow-up: synchronous distant leader registration

The live database confirms all four audited distant spawns are present in187 with
native scripts and restored source positions. Preparation now obtains Almyra
first and, after loading/activating each audited instance, explicitly assigns its
reverse Almyra GUID. Controller registration/INITIALIZE_DONE follows only after
the actor confirms that reverse link. Four leader AIs expose only this validated
controller binding; active-wave reassignment and native script/phase/map checks
remain guarded. The controller's running state prevents synchronous rebinds
once the shared event has started. Sylvanas continues its existing retry until
cinematic Liam/king links become available; Genn retains finale Liam refresh.

A native fixture clears all four controller links while leaving those actors
loaded, then invokes actual preparation/start without running their pending AI
initializers. It verifies both directions and all four acknowledgements. This
covers the dependency on delayed ticks previously missed by prelinked fixtures.
Failed readiness now names Lorna, Darius, Genn or Sylvanas individually. Requires
new server binary; no new SQL is needed. Missing dialogue rows still require the
previously specified2026_10_11_09 world update. Client verification remains open.


### Battle army run-speed units

Live verification confirms battle start and dialogue now work but actors move
slowly. All16 battle-file MOVE_RUN assignments now use SetSpeedRate instead of
SetSpeed. The prior1.2 absolute value was1.2m/s, not20% faster running; rate1.2
means approximately8.4m/s with the7m/s base. Liam reset uses native rate1.0.
Commander wave movement, following militia, artillery helpers/cannons and finale
followers retain original routes, SetWalk(false), timers and dialogue. Fixtures
now distinguish absolute speed from rate and assert actual8.4m/s movement across
six leaders, cannon/helpers and militia. No SQL or production-server changes.


## Battle stops at the third-wave gathering point

`WorldObject::SelectNearestPlayers` visited `GridTypeMapContainer`, which has no Player type. Players are stored in `WorldTypeMapContainer`. Switch this player-only search to `Cell::VisitWorldObjects`; preserve its radius/alive predicates and the quest helper's map, phase and incomplete-quest gates. This fixes the first player-presence gate at wave 3 without skipping any leader arrivals. Cannons are intentionally parked at Lorna wave-3 point 7 and are not part of the arrival mask.

The six allied commanders already zero combat damage. Add the same protection to Krennan, the event starter. Preserve cinematic Liam and enemy encounters. The synchronization fixture now executes the production player selector against separate grid/world visitors and verifies seven actual allied DamageTaken methods. Full gameplay confirmation remains required.


## Retry distant leader registration before the battle

Player testing found that visiting Darius and Genn made the start gate pass. The starter's 2.5-second readiness heartbeat only activated distant actors and searched for Almyra; it did not perform the bidirectional registration used by the gossip preparation. Reuse `PrepareBattleController()` on each idle heartbeat so actors loaded or respawned after an earlier attempt are linked and acknowledged without requiring their AI initialization event to tick. Running battles remain protected by the existing preparation guard. A native regression now clears all four late links and executes the production heartbeat before starting the battle, without ticking their AI or visiting their staging locations. Real client verification is still required.


## Quest 24902: Tobias wall crossing and route endpoint handoffs

Live DB confirmed all five native route counts (2/2/4/6/24); the escort stopped despite a nearby owner. Native waypoint movement constructs a direct multi-point spline without navmesh routing; the quest depends on specific last-node callbacks. Tobias now traverses these same five route parts as individual pathfinding MovePoint movements, with unique phase/point IDs and duplicate-callback guards. The first part starts through the three audited door-approach points from the existing walking fallback. Keep the native moat/wall/hiding jumps, player pauses, outside-event dialogue, owner checks and final Sylvanas conversation. The existing fallback for missing/malformed paths remains unchanged.

No SQL required. Three native fixtures verify all 38 native points plus the three exit points, wrong/duplicate callbacks, owner departure/return, actual first jump and second-part handoff, final dialogue and partial-summon cleanup. Geometry and full escort behavior still require a client playthrough with the server's maps/vmaps/mmaps.


## Tobias remains a noncombat scene guide

The final native escort point hands off to jump 2004; arrival schedules water positioning and the three Sylvanas-scene actors. Sylvanas arrival 2005 starts the conversation once. Existing dialogue regression executes all eight talk groups and verifies owner-only credit, followed by actor cleanup eight seconds later. Tobias retains the manual-summon lifetime cap of ten minutes, with cleanup on owner logout/death/quest cancellation or scene failure. Normal completion keeps him present until the end of the scene.

Make only the summoned map-654 Tobias guide passive, disable line-of-sight/AttackStart/CanAIAttack, zero incoming combat damage and remove melee updates. Ignore combat evade to prevent default evade Reset from stopping the escort. Persistent Tobias retains default AI via the existing GetAI guard. Native tests verify the final jump-to-scene scheduling and actual passive/damage/attack methods. Client verification remains pending.


## Tobias jump API argument order

The actual core signature is `MoveJump(x,y,z,orientation,speedXY,speedZ,id,...)`. Four Tobias calls supplied six arguments, omitting orientation: callback IDs 2001/2003/2004 became vertical speeds and the actual ID defaulted to EVENT_JUMP. Insert orientation 0 (unused because hasOrientation defaults false) into all native and fallback jump calls. The native fixture now matches the real seven-argument signature and validates XY/Z speeds and callback IDs for moat, wall and hiding jumps, using the recorded first-jump ID to continue the escort. No SQL changes. Client jump/landing verification remains required.


## Quest 24902 ruRU names and dialogue

`2026_10_12_00_world_gilneas_tobias_ruru.sql` restores five Russian NPC names and binds all 15 stock creature_text groups to matching BroadcastText IDs. Russian strings come verbatim from the supplied hotfix dump; see `docs/audit-data/gilneas-tobias-dialogue-ruru.json`. This includes five Tobias groups, four Sylvanas groups, three Warhowl groups, two Crenshaw groups and the outside Forsaken general. Some groups are reserve lines not currently invoked by the script. Remove only stock placeholder Sound 19606; native BroadcastText sound selection remains available. No invented audio or translated voice files.

Missing stock groups can be inserted; custom text/broadcast IDs/scripts and nonempty custom Russian names/translations are preserved. The locale table's primary key excludes Locale, so never overwrite an existing foreign-language row. BroadcastText binding provides the client locale fallback. The regression executes the portable statements using SQLite to verify first/repeat import, stock repairs and preservation; local MySQL execution was unavailable because the previous disposable MySQL binaries are absent. CI includes the regression; a real MySQL import and client display/voice check remain needed. Apply this world SQL or enable normal DB updates, then restart worldserver. No production database was modified.


## Tobias run speed and route/scene lifetime separation

Use normal MOVE_RUN rate 1.0 and SetWalk(false) for both native and fallback escort points; leave the other scene actors and jumps unchanged. Mark the owned guide active so its owner checks continue outside nearby player update cells. Remove the independent UnSummon(600000) event. The manual summon is now removed by the existing checked AI lifecycle: 15 minutes for the route, and a fresh three-minute budget after all three scene actors are successfully created. Logout/death/phase/map/quest-invalid owner and partial summon failures still clean up immediately; normal dialogue completion still removes Tobias eight seconds after credit.

Three native fixtures pass, including survival beyond the former ten-minute route cap, separate bounded scene time, successful scene budget reset and final dialogue cleanup. No SQL required. The reported premature disappearance is consistent with the old timer but needs another client playthrough to confirm resolution.


## Diagnose missing credit after the final Sylvanas line

Live DB reports SpecialFlags=2 and no quest objectives. Do not alter its requirements or force-complete the quest. The previous final callback marked completion and departed regardless of the result of AreaExploredOrEventHappens/KilledMonsterCredit. Only mark completion and schedule departure/cleanup after GetQuestStatus is COMPLETE. A failed credit attempt now leaves actors in place until the existing bounded scene timeout and emits a scripts error. Also log missing/invalid Tobias at the final gate and owner presence/alive/map/phase/status plus lifetime/stage when Tobias's lifecycle aborts.

Native dialogue regression now models quest-status change on a successful event and injects failed completion, verifying no departure/despawn and a diagnostic. The real cause of the reported disappearance/missing credit is not yet confirmed; a client reproduction and emitted log are required. No SQL change.


## Tobias summon-factory lifetime overwrite

Player log contains the final missing/invalid Tobias credit gate but no Tobias owner-lifecycle stop message. Core audit found WorldObject::SummonCreature calls Map::SummonCreature (which invokes IsSummonedBy), then applies its requested TempSummonType. SpellEffectSummonType can use that wrapper, overwriting the guide's manual type with a timed type after its initialization. Reassert MANUAL_DESPAWN in the owned guide's UpdateSceneOwner on each tick. TempSummon::Update calls Creature::Update/AI before checking its own type/timer, so this prevents the external timer from expiring the actor, while the existing owner-checked route/scene timeouts and end-of-dialogue cleanup remain authoritative. No global summon behavior changes.

Native regression injects the factory's post-initialization timed-type overwrite and verifies the guide survives the original three-minute expiry and the final conversation, reverting to manual type. Three native fixture suites pass; client confirmation pending.


## Quest 24920 ground-only bat and empty action bar

Keep custom flight AI enabled with OnCharmed override. After validating the owner, paths and vehicle kit, the summoned38540 explicitly boards its player in seat0 and stays active. Set flight speed with SetSpeedRate(2.0), about14m/s, instead of absolute4m/s. Increase the fallback return timeout to15 minutes; preserve explicit72849 return and native landing endpoints. Reassert the owned summon manual type during AI updates to avoid factory expiry overwriting initialization.

`2026_10_12_01_world_gilneas_bat_vehicle.sql` makes38615 a spellclick source rather than a controllable stationary641 vehicle, casts72472 from the clicking player, keeps641 on personal38540 and populates action slots1/5 with72246/72849. DB2 SpellEffect confirms72246 triggers missile72247, which applies damage; do not put the damage-only effect on the control bar. Preserve custom scripts/spells/vehicle IDs. Also ensure the prior `2026_10_06_12_world_gilneas_bat_flight.sql` route/phase update has been applied BEFORE this new update.

Native fixture tests auto-boarding request, charm retains AI, actual14m/s, manual summon ownership, timeout/return/landing and invalid riders/routes. Portable SQL fixture checks first/repeat/custom/unrelated preservation (SQLite semantics; local MySQL binaries unavailable). Client flight, control-bar display, bomb hits/6+40 credits and landing remain to verify. No live server or DB modified.


## Captured bat boarding after the summon spell

The first explicit EnterVehicle ran inside the active72472 summon effect. Unit::EnterVehicle casts46598 using only IGNORE_CASTER_MOUNTED_OR_ON_VEHICLE, not full triggered cast flags; an overlapping summon cast can therefore block it. Defer owner boarding until a subsequent AI update (initial500ms), then retry at most once per second within the existing ten-second unboarded bound. Never switch the owner out of another vehicle, and revalidate phase/quest/routes before retrying. Successful PassengerBoarded still starts flight once. Emit a console error when the boarding bound expires. Native regression verifies no cast during IsSummonedBy, deferred request, throttle and recovery after transient rejection. Client confirmation pending; no SQL changes.

## Quest 24679: missing Aderic tomb spell focus
Item 51956 invokes spell 72853. Client SpellCastingRequirements requires focus 1643;
SpellEffect supplies offering object 202319 and credit 38147. The world dump has
focus template 201964 (type 8, Data0 1643, Data1 10) but no corresponding Gilneas
spawn. Restore an inert always-visible focus at the player-measured tomb position
(-1621.367188, 1897.508057, 20.0), map 654. The native spell performs credit;
no NPC AI or quest objective changes. SQL checks the template before inserting,
allocates a free GUID and skips an existing equivalent focus on repeated import.
Local SQLite migration checks pass; actual MySQL import and client use remain
pending. Apply 2026_10_12_02_world_gilneas_aderic_tomb_focus.sql to the world DB
and restart worldserver. This SQL-only fix does not require recompilation.

## Quest 24679: corrected tomb elevation and position
The player confirmed the focus exists, but fresh client measurements at the actual
visible tomb place the player at Z approximately 30, X -1639 to -1646, Y 1902 to
1907. The original supplied point (-1621.367188,1897.508057,20) is too far away.
The follow-up migration relocates only the inert focus at that old point to
(-1643,1904,30), area 4727. All four new player samples are within five metres
of this point. It preserves the native template radius and unrelated/custom spawns;
it can also insert the missing focus if the prerequisite template is present.
Apply 2026_10_13_00_world_gilneas_aderic_tomb_position.sql and restart worldserver;
no binary rebuild is required. Client quest completion remains to be confirmed.

## Quest 24681: glaive thrower, outriders and Legion level scaling
Audited desktop world dump: quest objectives are 37916 x40,37938 x8,37921 x4.
37927 has native spells 70735/70732/59737 but VehicleId 0 and no persistent spawns;
38150 also has no spawns. Restore one directly boardable 37927 beside the audited
quest giver 38149 (GUID804189) in phase189. This uses existing glaive Vehicle447,
seat4806 (client copy of2021, CAN_CONTROL flag present). It is a shared directly
boarded vehicle, not the previously unconfigured personal summon from71238.
The harbor point is offset three metres from the known quest-giver spawn; ground
placement and vehicle controls require client verification. Native abilities and
ordinary kill credit are retained, with no automatic completion or objective edits.
37939's accessory37938 already exists, but ObjectMgr rejects it without a wolf
spellclick row. Add NPC-only ride46598 (do not expose spellclick to players), and
change invalid accessory summon type0 to DEAD_DESPAWN7. Keep minion0 so the
native dismounted rider is not forcibly killed with the mount.
Add missing level-scaling rows5..20,zero delta for37884,37885,37916,37921,37938,
37939 and the restored glaive. Preserve existing scaling overrides, custom scripts,
health/damage multipliers, existing spawns and all quest objective amounts.
SQL:2026_10_13_01_world_gilneas_glaive_and_scaling.sql; no C++ rebuild needed.
Local SQLite checks cover boarding config, accessory type, scaling preservation,
repeat import and missing/custom guards. MySQL import and full client completion
are pending. Verify: visible harbor glaive, single driver, three abilities, targets
40/8/4, mounted riders, levels relative to players5..20, and leaving/reboarding.
Reference mechanics: https://warcraft.wiki.gg/wiki/They_Have_Allies,_But_So_Do_We

## Quest 26706: boarding, scene dialogue and Russian text
World-dump audit finds Vehicle641/native AI on43751 but no npc_spellclick_spells
row: Tobias's runtime flag cannot board players without ride46598. Add this
binding only for the native template, retaining the ship departure window.
Tobias43749 used reversed text groups: group0 is waiting, group1 is boarding.
Correct all window announcements and refresh nearby hippogryph GUIDs each window
so respawned birds are not omitted by a stale cache.
Override OnCharmed on both43751 and escape43713 to retain scripted route/owner
state when a control seat charms the NPC. Existing owner, death, dismount, quest,
phase and once-only arrival credit guards remain. Flight4375101 has eight points;
after it the bird approaches onboard Lorna43566 and hands the player to her scene.
The ship stage clears rafters, enables ropes, descends decks, plants three charges,
fights43567, and creates owner-bound escape vehicles. Escape4371301 triggers
credit43729 only after arrival; world quest objective254200 requires this credit
once. Quest ender43727 exists in the dump. No instant quest completion added.
Correct Lorna's Talk groups to the eight actual rows0..7 (old calls8/9 were missing).
SQL2026_10_13_02_world_gilneas_endgame_boarding_ruru adds11 missing Russian
scene translations, restores the dump's official Russian quest description when
absent, and supplies Russian progress/reward text. Scene/progress/reward translations
are authored translations; this does not claim extracted official Russian voices.
Existing custom locale and foreign locale rows are preserved. Existing sound IDs
are unchanged. Apply earlier2026_10_10_00_world_gilneas_endgame_routes.sql if the
routes are absent, then the new boarding/localization update and install new code.
Local native fixtures pass: incoming flight/lifecycle, outgoing flight/arrival credit,
three charge and boss creation, same-ship floors and battle ownership. Added charm
regressions simulate default AI disabling, proving the custom AI remains enabled.
SQLite locale/boarding checks pass first/repeat/custom/foreign cases. Actual MySQL
import, transport geometry/animation, and complete client passage remain pending.
Reference sequence: https://www.wowhead.com/quest=26706/endgame

## Quest26706: actual transport passengers and startup readiness
The user confirmed all five required groups are still on map0 in the live world DB:
42141x22,43566x1,43651x4,43703x4,43793x15. Transport203428's template uses
SpawnMap749 (Data6); Transport::LoadStaticPassengers reads only that map. The
previous boarding/locale patch therefore did not address this structural blocker.
SQL2026_10_13_03_world_gilneas_endgame_transport_passengers relocates94 audited
map0/phase191 local-offset spawns to749. Each update checks exact GUID/entry,
phase, no custom spawn script and all three recorded coordinates. Offset coordinates
remain unchanged; zone/area are cleared because the transport uses a separate map.
Persistent boss804845 is excluded because Lorna creates43567 at its scripted stage.
Restore two rope gameobjects at the recorded upper-deck rope-anchor offsets; retain
native template go_rope_204428. Do not create duplicate objects on repeated import.
Also correct harbor clickers43747/spell81877 cast_flags0->1. Client data shows
81877 summons43751 with property1201 (copy689,Control4/categoryvehicle); the
core then performs native automatic seat0 boarding.43751 itself is not the harbor
clicker, so the previous43751 spellclick row alone was insufficient.
Tobias now polls readiness every second, activates the ship grid and requests static
passenger loading only if empty. It checks named roles: one enabled living Lorna,
four warriors,four sharpshooters,22 loaded guards (defeated ones allowed),15 living
jump anchors and two actual rope objects. It does not blindly trust passenger39.
The ship records its native boarding-window state even before Tobias is loaded and
replays it at late registration. The departure cycle is preserved: a fresh server does
not imply immediate boarding if the ship is in the departure/travel stage. Readiness
also requires the native arrival window. No forced teleport or fabricated completion.
A throttled30-second server log starts with 'Gilneas26706 readiness'; it reports
missing ship/closed window or individual role counts/ready. Only quest players
trigger this diagnostic check. Restart after importing SQL and installing new code.
Local actual-method fixtures and SQLite migration tests pass. They cover late
registration, empty/full/missing/dead crew, missing ropes, cycle gates,94 recorded
coordinate preservation, repeat and custom/unrelated guards. Full client passage
and the deployed server's resulting readiness log still require confirmation.
Previous GCC and Windows builds752bcb8 succeeded. Its MySQL regression failed
because the new locale fixture shadowed an existing module; restored the original
MySQL route suite and renamed the locale fixture to endgame_locale_database.

## Quest26706: incoming flight speed after client boarding confirmation
User confirmed boarding now works, but the hippogryph flies very slowly. The AI
used SetSpeed(MOVE_RUN,3/4.9/2), which means absolute metres per second, not
speed multipliers. Replace with rates for both RUN and FLIGHT because waypoint
splines choose their speed from current movement flags. Takeoff rate2=14m/s,
cruise rate3=21m/s after callback2, final approach rate1=7m/s after callback6.
Route4375101, arrival callbacks and ownership/handoff remain unchanged. These
are chosen travel speeds, not a claimed exact retail measurement. Native fixture
now checks actual speed rates for both movement modes at all three stages and
passes locally. No SQL needed; install rebuilt script binaries and restart.

## Quest26706: physical ship visibility and actual docking events
User confirms the ship is visible only with GM ON. Native transport28/203428 has
phase0 while its onboard actors are191. Correct only the untouched native transport
to phase191 using2026_10_13_04_world_gilneas_endgame_ship_phase.sql; do not make
all transports always visible or change player phases globally.
Actual client TaxiPath2338 node53698 is the rendezvous at(-1465.76,3251.48,93.84),
with180-second stop: arrival25670,departure25664.25663 is later departure near
(-871,1866,158);25727 is still later destruction. Previous event mapping opened
boarding at the wrong side of the route. Correct ship state and Tobias announcements
so only25670 opens it; other three events close it. Preserve heartbeat scheduling
when events reset Tobias's EventMap. Late registration still replays current state.
GetData readiness now checks actual transport timer/keyframe docking interval and
requires120 seconds until departure, allowing the faster bird to reach the ship
before it leaves. Native fixture covers arrival, departure, destruction, exact120s
boundary and expired stop even before event callback. SQL tests cover phase,
repeat/custom/unrelated transport preservation. Full GM-OFF client arrival remains
to be tested; timing margin is chosen conservatively, not a retail exact measurement.
