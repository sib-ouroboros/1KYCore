# Восстановление Гилнеаса по результатам клиентского прохождения

ТЗ остаётся открытым. Это первый пакет исправлений после новых сообщений из игры,
а не подтверждение полного восстановления 14 заданий. Рабочий сервер не изменялся.
Исходный HEAD: `1927cfe139e8b1961bf4c0f113623bc0a50fd083`.
Целевой клиент — 26972; доступные локальные DB2 ранее определены как 26654.
Строка ревизии и SQL ledger работающего сервера независимо не проверены.

## Подтверждённые исправления

- 14465: ворота 196399/196401 принимали только INCOMPLETE, хотя лошадь уже
  разрешала COMPLETE. У задания нет целей, поэтому состояние COMPLETE после
  принятия допустимо. Теперь оба состояния допускают открытие ворот; кулдаун,
  закрытие и прежний допуск дилижанса Исхода сохранены.
- 24468: явное начало ответной атаки свободного кроколиска. Сохранены отсутствие
  взаимного урона сценических NPC и обычный урон игрока. Зачёт остаётся штатным
  за убийство 37078; искусственного credit за приближение не добавлено.
- 24575/24674: у 37701 отсутствует scaling при min5/max20. SQL добавляет только
  отсутствующую строку для неизменённого шаблона, используемого исключительно
  на карте654. Диапазон сохранён; delta0 — обоснованное предположение, а не sniff.
  Уже существующие scaling, custom AI/скрипт/уровни/faction и другие карты защищены.
- 26706: исправлены callbacks гиппогрифа. NPC-пассажир не удаляет транспорт;
  чужой игрок не перезаписывает владельца; дубли посадки не создают повторный
  вылет. Прерывание очищает очередь и освобождает собственного пассажира.
  Маршрут, штатные координаты, корабль и конечный credit не заменялись.

Проверены реальные извлечённые production handlers с подставленными границами
мира и scheduler. Локально строгий C++ PASS: manor_gates, endgame_transport,
survivor_combat, transport и scaling. Проверка scaling включает уровни
1/4/7/10/12/15/20; вычисление HP/урона в ней подставлено и не считается боевым тестом.
SQL проверен на отдельной MySQL8.0.45 копии: первый/повторный импорт, custom
scaling/AI/границы/faction, отсутствие спавнов Gilneas, смешанные карты и
сохранность остальных данных. Тестовая схема удалена. CI проверяет sanitizers
и весь существующий изолированный SQL-пакет Гилнеаса.

Дополнительно восстановлены17 уникальных мест Disturbed Soil201871 для24602
по исходным координатам из пинованного LegionCore SQL (SHA256 в отдельном
`gilneas-memento-restoration.json`). Из32 исходных записей исключены15 дубликатов.
Фаза188 подтверждается существующим questgiver38144/GUID803966.
Штатный loot49921 остаётся100% quest-required; предметы собираются через объект.
SQL сохраняет пользовательские spawns/GUID/шаблон/loot/objective/фазу выдающего NPC.
Первый и повторный импорт, все guard-сценарии прошли отдельную MySQL проверку.
На локальных51 MMAP-тайлах654 все исходные позиции нашли ground polygons.
Это не измерение реального terrain/VMAP и не клиентская приёмка.

## Остальные участки

| Задание | Что ещё требуется |
|---|---|
| 14293 | Высота/анимация Креннана, фактический поиск пушки, фаза и хореография выстрелов |
| 14400 | Живые PhaseShift игрока/объекта, respawn, видимость и Lock1691; нулевые PhaseId/Group не доказывают исправность |
| 14416 | VehicleSeat, action bar и доставка 5/5 на26972 |
| 14465 | Реальное прохождение ворот/пути и высадка; прежний native endpoint test сохранён |
| 24438 | Terrain/VMAP/actual spline/hover по всем33 точкам; прежний Detour PASS недостаточен |
| 24468 | Боевые пары в фактических спавнах/фазах, вмешательство двух игроков и штатный зачёт5/5 |
| 24575/24674 | Ключи/цепи, Brothogg37802 и боевые HP/урон после масштабирования |
| 24904 | Живой FSM/регистрация актёров/фазы и применение прошлых SQL, затем все волны и финал |
| 24902 | Подтверждённые5 исходных путей; текущий fallback не равен Blizzlike-маршруту |
| 24920 | Seat/control flags, загрузка путей, реальный воздушный spline и бомбардировка/возврат |
| 24602 | Проверить восстановленные17 объектов обычным игроком: видимость, Lock43, получение предмета49921 и сбор5/5 |
| 24679 | Spell предмета51956, цель38147, могила и подтверждённая памятная сцена |
| 26706 | Полный корабельный FSM, путь4375101, passengers, бой, уничтожение и escape credit43729 |

Аудит release-base содержит293 шаблона карты654. Кандидаты с диапазоном уровней
без scaling перечислены в JSON, включая дружественных NPC: автоматически
применять к ним тот же SQL нельзя. Это не копия базы со всеми обновлениями.

## Источники и приёмка

Исторические ориентиры: [14465](https://www.wowhead.com/cata/quest=14465/to-greymane-manor),
[14416](https://www.wowhead.com/cata/quest=14416/the-hungry-ettin),
[24904](https://www.wowhead.com/cata/quest=24904/the-battle-for-gilneas-city).
Они подтверждают общие цели и начало событий; детали26972 требуют отдельной проверки.
Пинованные прежние источники координат и ограничений сохранены в audit-data.

Все14 строк имеют CLIENT_TEST_REQUIRED. Для обычного нового воргена проверить
GM OFF, GM ON→OFF, abandon/reaccept, death, relog/disconnect, два игрока,
рестарт и повторный запуск другим персонажем. Не использовать `.quest complete`.
Файлы `gilneas-client-bugs.json` и `gilneas-route-validation.json` разделяют
исправленный дефект, частичный automated PASS и неподтверждённое прохождение.
Отсутствующие runtime-измерения отмечены null; координаты не выдумывались.


## 2026-10-10: связка уничтожения корабля и эвакуации26706

Проверки предыдущего3250544 завершились успешно: GCC37952293602,
Windows37952298607 и Gilneas client bug regressions37952269840 (native+MySQL).
Это не клиентское подтверждение цепочки.

Выявлены и исправлены новые ошибки production code:

- Лорна читала GUID из каждой виверны, но использовала собственный последний
  m_playerGUID для всех посадок. У виверны вообще не было GetGUID override.
  Теперь каждому подходящему участнику назначается его собственный транспорт.
- Создание транспорта ограничено живыми участниками26706 на том же корабле,
  карте и в совместимой фазе. Посторонние/уже сидящие игроки не захватываются.
  Неудачный CreateNPCPassenger проверяется перед разыменованием; есть ERROR.
- Раньше любое снятие пассажира ставило событие выдачи43729. Теперь досрочная
  высадка отменяет полёт; credit допускается только после штатной точки2
  маршрута4371301 и высадки. Это не отдельное доказательство взрыва судна.
- Владелец неизменяем, NPC/чужие callbacks не завершают чужую поездку,
  дубли посадки и arrival не повторяют события. Отмена/death/logout/смена карты,
  фазы или vehicle очищает очередь без credit. Reset освобождает собственного
  активного пассажира. Перед delayed credit снова проверяется состояние игрока.

Старый финальный TeleportTo оставлен после штатного callback; нового телепорта
вместо отсутствующих участков пути не добавлялось. Его соответствие retail
эвакуации, взрыву и целевому26972 по-прежнему требует проверки.
Добавлена DEBUG-трассировка ESCAPE_WAITING/OWNER_BOUND/BOARDED/START/ARRIVED/
CANCELLED/COMPLETED с GUID транспорта/владельца и текущими флагами.
Она относится к эвакуации; полная диагностика корабельного FSM остаётся задачей.

В уже пинованных47 архивах Arkania/ArkCORE-NG найдено10 исходных маршрутов:
4375101 (8 точек),4356601–4356607 (29 точек),4356701 (8),4371301 (3).
Всего48 точек. Исходник2016_07_30_00 даёт базовый подлёт;2017_05_25_00 заменяет
его точки6/7 и даёт остальные маршруты. Полные SHA256 и нумерация в
gilneas-endgame-source-routes.json. Никакой другой SQL архивов не переносился.
В read-only release-base все10 групп отсутствовали; это не независимая
проверка deployed базы. SQL2026_10_10_00 добавляет только целиком отсутствующие
группы при исходных bindings/VehicleID, сохраняя даже частичные custom маршруты.
Координаты Лорны/противника/виверны — transport offsets: проверять их как
мировые точки terrain/MMAP654 было бы неправильно. WaypointMovementGenerator
явно поддерживает transport offsets. Координаты и режимы движения не придуманы.

Локальные native fixtures: полный AI виверны и реальные creation/boarding cases
Лорны — PASS с -Wall/-Wextra/-Werror. Проверены два владельца при устаревшем
GUID Лорны, ошибка создания, фильтрация участника, once completion и все
перечисленные отмены. Мир/vehicle/scheduler подставлены; фактический spline,
модели/seat/коллизия и взрыв не воспроизводятся fixture.
Изолированная MySQL8.0.45 — PASS:48 точек, точные исходные поля, повтор,
сохранение10 частичных/custom групп, guardsbindings/VehicleID и других таблиц.
Тестовая схема удалена. Проверки включены в существующий Gilneas CI.

Остаётся CLIENT_TEST_REQUIRED: полный подлёт→бой→канаты→противник→взрыв→
эвакуация→сдача, runtime transport passengers/readiness и повторная попытка.
Наличие48 waypoints и fixture PASS не закрывают26706 или общее ТЗ.
Рабочий сервер не обновлялся.


Дополнительная проверка создания: CreateNPCPassenger инициализирует DB PhaseShift
из новой CreatureData (без фазы игрока). Перед посадкой личная виверна теперь
получает штатный PhasingHandler::InheritPhaseShift от своего владельца.
Проверка creation→boarding включает владельцев/Лорну в188 и изначально
созданные машины в другой фазе. Native вызов использован в production;
граница PhasingHandler в fixture подставлена. Клиентская видимость ещё не проверена.


### 2026-10-10: Endgame transport creation failure audit

Lorna's native `EVENT_TALK_PART_09` and `EVENT_SPAWN_OBJECT` unconditionally
dereferenced three `CreateGOPassenger` results and one `CreateNPCPassenger`
result. Both native transport factories explicitly return null when DB creation,
position validation, or map insertion fails. Each gunpowder object now receives
scale and grid registration only after successful creation; a failed object is
logged and the remaining objects are still attempted. A failed orc spawn clears
the stale actor GUID, logs the failure and does not schedule actor movement.
No replacement actor, quest credit, retry loop, coordinates or phase changes
are introduced. Successful scene timing and original routes remain unchanged.

`test_gilneas_endgame_scene.py` compiles and executes the actual two production
switch cases. Controlled factory boundaries cover all three individual barrel
failures, successful creation, failed orc creation, registration, original offsets,
scale and event scheduling. Local strict C++ tests passed, including adjacent
escape AI tests. The new fixture is included in sanitizer CI. These fixtures do
not execute transport geometry or prove the full ship scene in the client.

At this audit, cd06a45 GCC and the complete Gilneas native/MySQL workflow passed;
its Windows job was still running. All three workflows for 8480825 passed.
Full client acceptance of 26706 and the 14-quest recovery remains required.


### 2026-10-10: Endgame participant and floor checks

Lorna previously let any nearby player satisfy range gates or block progress
with combat. `IsSceneParticipant` now limits both checks to alive players with
26706 incomplete, on map 654, visible in Lorna's phase and on the same transport.
Range checks scan all nearby players, so a nearer outsider does not mask a
valid participant. Existing range values and wait timings are unchanged.

Floor cleanup previously counted any attackable unit with a similar transport
offset Z, including units on other transports or units without a transport.
It now counts only native gunship grunts 42141 on Lorna's transport and in her
phase. The existing attackable-unit query retains its alive-target filtering;
floor heights, distances and dialogue conditions remain unchanged.

The native four-method fixture `test_gilneas_endgame_gates.py` covers participant
combat, outsider combat, outsider-first range selection, quest loss, death,
map/phase mismatch, another ship, no ship and both native floor heights. World
selection boundaries are controlled; full scene/client acceptance is still open.
No SQL, teleport, credit or production-server changes are part of this package.
All GCC, Windows and Gilneas native/MySQL jobs for ca8a192 passed before this work.
