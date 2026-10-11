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
