# Перенос SylvaniaCore без игроков-ботов — 30.09.2026

Источник: BlaMacfly/SylvaniaCore, ветка sylvaniacore.
Предыдущий импорт: d4f9f5946a1a1c2ff8fd8aa04b2992828f63482c.
Новый снимок: a6145c22e9ad6ac69690d4a2f7794bae4e1caf95 (50 последующих коммитов).
Наша база перед переносом: 0633cf3b24af2bcba6b3aaac8a672e69f6d9e911.

## Перенесено

- Кампании оплотов 12 классов, их NPC, фазы, задания и данные миссий.
- Выдача заданных миссий оплота, сохранение предложенных миссий и формат открытия стола миссий 7.x.
- Исправления артефактов, обязательных/необязательных целей заданий, выбора следующих артефактов.
- Расколотый берег: отдельные критерии Орды, высадка, мост, движение и роли лидеров; связанные задания Даларана.
- Добыча Конклава Ветра, транспорт Трона Четырёх Ветров, обмен жетонов T11.
- Полное upstream-удаление Discord-релея, Graylog-аппендера и зависимостей CPR/cURL.
  Удалён также ранее сохранённый нами потребитель очереди Discord в Main.cpp.
- Четыре ранее отложенных изменения AuctionHouseBot из диапазона 2a526e2..d4f9f59.
  Аукционный бот сохранён проектом и не является удалённой системой игроков-ботов.

Большое число файлов объясняется зависимостями: из 546 переносимых путей 474 удаляются.
Для каждого удаляемого файла подтверждено, что наша версия совпадает с прежней upstream-версией.

## Исключено и адаптировано

15 изменённых файлов BotAI/BotAITool/BotClassAI/BotDuelAI/BotFieldAI/BotGroupAI/MercenaryMgr
не возвращаются. Изменения BotAITool относятся только к уже удалённым поискам NPC/добычи
и не нужны общей PlayerGameplayUtility.

В scenario_broken_shore_intro сохранены новые таблицы критериев Орды, но не возвращены
DoOnVraisJoueurs/IsPlayerBot и DismissFreeEscort. Вместо ботского фильтра остаётся
штатный DoOnPlayers. Исходное исправление AddSC_boss_shiwar уже совпадает с upstream.

Сохранены наша очистка, миграции удаления служебных таблиц, русский README, тесты,
исправление определения активной специализации и безопасное закрытие БД при
--update-databases-only. В Player.cpp/.h добавлена только выдача миссий по заданиям;
остальные отличия нашей ветки сохранены. Main не изменяется.

## Проверка и развёртывание

До применения проверено подготовленное дерево: нет возвращённых зависимостей PlayerBot,
MercenaryMgr, CapitalSiege, Discord/CPR/Graylog; нет маркеров конфликта. Полные сборки
и регрессионные проверки запускаются после публикации. Игровая приёмка кампаний,
сценариев и миссий оплота не заменяется успешной компиляцией.

SQL переносится в исходные каталоги upstream. sql/sylvania не является каталогом
автоматических миграций: обновление бинарников само по себе эти исправления БД не применяет.
Рабочие БД в этом переносе не изменялись; старые миграции sql/updates не переписывались.
Перед применением новых контентных SQL нужен снимок БД и пробный прогон на копии.
Старый пакет DB735.02 и опубликованные дампы этим переносом не перезаписываются.
Существующие настройки Discord/Graylog больше не обслуживаются новым кодом.

## Новые/обновлённые ручные SQL

Ниже файлы в порядке последнего изменения в переносимом диапазоне. Это обзор источника,
а не утверждение о выполненном импорте или совместимости с произвольной внешней БД.

- `sql/sylvania/rivage_passerelle.sql`
- `sql/sylvania/rivage_postures_mouvements.sql`
- `sql/sylvania/rivage_p7_horde.sql`
- `sql/sylvania/jetons_t11.sql`
- `sql/sylvania/conclave_butin.sql`
- `sql/sylvania/objets_fin_prets_horde.sql`
- `sql/sylvania/quete_fin_prets_horde.sql`
- `sql/sylvania/recrues_horde_positions.sql`
- `sql/sylvania/quete_fin_prets_horde_mukar.sql`
- `sql/sylvania/quete_bataille_rivage_horde_russo.sql`
- `sql/sylvania/rivage_passerelle_horde.sql`
- `sql/sylvania/quete_destin_horde_sylvanas.sql`
- `sql/sylvania/quete_emissaire_allari.sql`
- `sql/sylvania/trone_quatre_vents_slipstream.sql`
- `sql/sylvania/quete_demons_parmi_nous.sql`
- `sql/sylvania/campagne_chasseur_legioncore.sql`
- `sql/sylvania/quete_40953_prerequis.sql`
- `sql/sylvania/aludane_menu_18723.sql`
- `sql/sylvania/objectifs_optionnels.sql`
- `sql/sylvania/spellclick_campagne_chasseur.sql`
- `sql/sylvania/campagne_voleur_legioncore.sql`
- `sql/sylvania/armes_prodigieuses_prerequis_34429.sql`
- `sql/sylvania/statue_ohnahra_cast_flags.sql`
- `sql/sylvania/campagne_paladin_legioncore.sql`
- `sql/sylvania/campagne_guerrier_legioncore.sql`
- `sql/sylvania/campagne_pretre_legioncore.sql`
- `sql/sylvania/phase_5934_emmarel_serment.sql`
- `sql/sylvania/nettoyage_portages_legioncore.sql`
- `sql/sylvania/campagne_mage_legioncore.sql`
- `sql/sylvania/campagne_demoniste_legioncore.sql`
- `sql/sylvania/campagne_dk_legioncore.sql`
- `sql/sylvania/campagne_dh_legioncore.sql`
- `sql/sylvania/emmarel_armes_suivantes.sql`
- `sql/sylvania/rat_de_bibliotheque.sql`
- `sql/sylvania/campagne_chaman_legioncore.sql`
- `sql/sylvania/campagne_druide_legioncore.sql`
- `sql/sylvania/campagne_moine_legioncore.sql`
