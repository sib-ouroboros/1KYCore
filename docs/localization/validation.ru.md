# Журнал проверки и оставшиеся приёмочные сценарии

## Выполнено в изолированной среде

Windows, Python 3.12, portable MySQL Community **8.0.45**, bind 127.0.0.1,
порт **33317**, mysqlx выключен, local-infile=0, secure-file-priv=NULL,
отдельный datadir вне репозитория. Системная служба не устанавливалась.
Исходный release world создан на MariaDB 11.4.7; повторение на точной
версии СУБД рабочей системы остаётся приёмочным тестом. Результат MySQL8
не выдаётся за тест MariaDB или MySQL5.7.

Подготовка world: verified release и 24 migration ветки, hotfix: verified release
и 1 migration frFR. Донор анализировался read-only, никогда не импортировался
как исполняемый SQL. Все сырые SHA перепроверены. Локализация применялась только
к `ru_target`/`ru_hotfix_target`. После испытаний данные восстановлены.
Все 24 применённые migration world прочитаны как UTF8; их исходные SHA
зафиксированы в target-world-migrations.json. Файлы ветки не менялись.


| Проверка | World | Hotfix |
|---|---:|---:|
| Пакетов | 184 | 341 |
| Полей | 22 565 | 40 091 |
| Таблиц с контрольными суммами | 248 | 368 |
| Все пакеты применены | PASS | PASS |
| Только allowlist-поля и собственные добавленные rows | PASS | PASS |
| enUS, остальные локали, игровая информация | PASS | PASS |
| Повторное применение без изменений | PASS | PASS |
| Чужая правка после генерации: отказ до записи | PASS | PASS |
| Чужая правка перед откатом: отказ до записи | PASS | PASS |
| Точный возврат checksum каждой исходной таблицы | PASS | PASS |
| Повторный откат без изменений | PASS | PASS |
| Прерывание после первой постоянной записи и retry | PASS | PASS |

Снимки всех затронутых locale-строк сравнивались по каждому полю и PK, включая
неизменённые столбцы и остальные локали. Для новых строк сверялся полный row hash.
Для всех остальных таблиц сравнивались CHECKSUM TABLE EXTENDED; после отката
сверялся полный набор таблиц, а не только количество записей.
Машиночитаемые результаты и пары исходных/восстановленных checksum находятся
в `test-result.json` / `database-checksums.json.gz` каждого непустого bundle.

Начальный прогон был остановлен из-за полного сканирования PK при BINARY-only
guard. Частично применённые пакеты восстановлены точным откатом. Итоговый
indexed+binary вариант заново прошёл все перечисленные проверки; SQL hash
доказательств относится только к окончательным пакетам.

На синтетических MyISAM и InnoDB отдельно подтверждены:
case-insensitive конфликт `ruru`/`ruRU`; запрет удаления добавленной строки
после чужой правки Other/VerifiedBuild; различие NULL/''; сохранение чужого
нецелевого поля при откате собственной правки существующей строки.

23 Python unit test: parser/escapes/многострочный SQL/NULL/duplicate/unsupported
syntax/invalid UTF8/chunk boundary; matching/source identity; сохранение текста;
gender/printf/fmt/link/length/CSV; gossip owner/action/box/foreign locale/Broadcast
priority; deterministic gzip/extract/tamper/path traversal.

Изолированный C++ harness с **GCC 16.2.0 (w64devkit 2.10.0)** компилирует
действительные helper и DB2Manager::GetBroadcastTextValue из исходников, с fake
store/session/Player. Проверены ruRU/enUS/третья локаль, male/female/none,
отсутствующий ruRU/entry, пустой default, mask ruRU при all-files/default-only
и исключение LOCALE_none. Flags: -std=c++14 -Wall -Wextra -Werror.
Windows-run **без ASan/UBSan**; Linux-тест по умолчанию включает sanitizers.
Это проверка функций с fixtures, а не сборка worldserver.

Дополнительно: повторный **полный разбор raw world/hotfix дампов без cache**
итоговым CLI дал побайтно идентичные 525 SQL-пары и provenance manifests.
Checkout из Git index сохранил source/catalog/gzip/SQL hashes благодаря LF
attributes для инструментов и JSON. 48 095 принятых полей отдельно проверены
по UTF8 bytes против фактических WriteBits в Quest/Query/NPC/Chat packets;
14 561 gameobject-поле использует NUL-terminated строки в sized payload и
проверено по DB limits. Подстановки клиента/printf runtime этим не симулируются.

## Команды для воспроизведения проверок

```sh
python3 -m unittest discover -s tools/localization -p 'test_*.py'
python3 tools/localization/test_argus_locale.py --root . --compiler g++
python3 tools/localization/test_packet_lengths.py --root .
# portable Windows: --no-sanitizers, фактический путь к g++.exe
```

Для отдельной disposable MySQL (без production credentials) создать подготовленную
тестовую world/hotfix базу и извлечь bundle. Экспорт manifest.json получается при
extract; `--packages` указывает каталог распакованных .sql:

```sh
MYSQL_DISPOSABLE_TEST_SERVER=1 python3 tools/localization/test_mysql_packages.py --mysql /path/mysql --port 33317 --database ru_target --packages /tmp/1ky-ru-world --manifest /tmp/1ky-ru-world/manifest.json --report /tmp/world-test.json
MYSQL_DISPOSABLE_TEST_SERVER=1 python3 tools/localization/test_mysql_packages.py --mysql /path/mysql --port 33317 --database ru_hotfix_target --packages /tmp/1ky-ru-hotfix --manifest /tmp/1ky-ru-hotfix/manifest.json --report /tmp/hotfix-test.json
MYSQL_DISPOSABLE_TEST_SERVER=1 python3 tools/localization/test_mysql_guards.py --mysql /path/mysql --port 33317
```

Тест допускает только localhost, явный scratch-name и нестандартный порт,
проверяет hashes SQL перед изменениями. Он использует scratch root без пароля
только в самостоятельно подготовленной disposable среде и `--no-defaults`.
Существующие рабочие mysql.cnf/credentials не читаются. В PowerShell установить
переменную `$env:MYSQL_DISPOSABLE_TEST_SERVER='1'` перед вызовом.

## НЕ выполнено: полный сервер и клиент

Полная сборка 1KYCore не выполнена: отсутствуют CMake, Visual Studio/toolchain
и полный набор зависимостей сервера. Portable GCC использован только для
изолированного regression harness. Ветка не отправлялась в CI, push запрещён.
Действующий worldserver не запускался, клиент не подключался. Не заявляются
проверки загрузки всех таблиц, прохождения квестов, sound или визуального кеша.
Перед merge требуется штатная Windows/Linux сборка проекта и тестовый worldserver.

### Приёмка сервером

На своей тестовой копии сделать baseline startup log, применить пакеты offline,
перезапустить с ruRU файлами и hotfix-локалями из README. Сравнить логи загрузки
quest/objective/page/gossip/CreatureText/DB2: нет новых missing reference,
неподдерживаемой locale, schema error, string truncation. Проверить наличие
ruRU в hotfix loader и прежний enUS fallback. После испытания остановить
сервер, откатить SQL и сравнить baseline.

### Приёмка в игре: реальные записи из результата

Для каждой категории ниже SQL уже проверен, клиентский результат пока pending.
Полные English/RU и известные Gilneas IDs: `game-test-samples.json`.

| Категория | Ключ | Поле | Статус |
|---|---|---|---|
| quests | 41244 | LogTitle | SQL проверен; сервер/игра не проверены |
| objectives | 251951 | Description | SQL проверен; сервер/игра не проверены |
| rewards | 10263 | RewardText | SQL проверен; сервер/игра не проверены |
| requests | 10468 | CompletionText | SQL проверен; сервер/игра не проверены |
| pages | 1031 | Text | SQL проверен; сервер/игра не проверены |
| npcs | 101511 | Name | SQL проверен; сервер/игра не проверены |
| objects | 100028 | name | SQL проверен; сервер/игра не проверены |
| choices | 265 | Question | SQL проверен; сервер/игра не проверены |
| responses | 265,584 | Header | SQL проверен; сервер/игра не проверены |
| gossip | 0,15 | OptionText | SQL проверен; сервер/игра не проверены |
| server_strings | 10056 | content_loc8 | SQL проверен; сервер/игра не проверены |
| broadcast | 96430 | Text_lang | SQL проверен; сервер/игра не проверены |

1. Создать отдельные ruRU/enUS тестовые аккаунты и персонажей обоих полов;
   сохранить client build 26972 и одинаковую тестовую сборку сервера. Добавить
   персонажа с максимально допустимым длинным именем для $n; не изменять
   реальных персонажей/их состояния для теста.
2. Для quest/reward/request/objective samples найти фактического giver/taker через
   creature_queststarter/ender и gameobject_queststarter/ender, посмотреть требования
   quest_template_addon/conditions. Если записей нет, отметить «не удалось
   подтвердить доступность», а не создавать спавны или обходить условия ради отчёта.
   Через штатное прохождение проверить получение, журнал, цели, промежуточный текст,
   сдачу/награду; ruRU показывает proposal, enUS — исходник. Игровые шаги совпадают.
3. NPC/object samples: найти существующий spawn и открыть query tooltip/диалог;
   сравнить оба языка, имя и альтернативную форму. Книгу открыть через связанный
   gameobject_template.PageID и пройти всю цепочку NextPageID без изменения связей.
4. Choice/response: найти сценарий, вызывающий существующий ChoiceID, проверить
   Question/Header/Answer/Description/Confirmation и прежний выбранный ResponseID.
   Где нет подтверждённого триггера, записать pending access, не симулировать успех.
5. Для gossip взять точный MenuId/OptionIndex, найти NPC по gossip_menu_id, открыть
   меню и подтвердить прежний ActionMenu/POI, стоимость/Box и отсутствие Broadcast
   override. Не менять чужую локаль, занимающую PK.
6. Для Broadcast найти реальную ссылку ID в creature_text/npc_text/gossip; проверить
   male/female, enUS fallback и связь с прежним NPC/group/text. Звуковые IDs остаются
   исходными. Для trinity_string sample проверить фактический command/message caller,
   достаточные права и printf аргументы, затем локаль enUS и ruRU.
7. Argus C++: обычным прохождением квеста 48440 дойти до NPC 120977 на карте 1750.
   На ruRU male/female кнопка должна быть «Я готов.»/«Я готова.», на enUS «I'm ready.».
   Нажатие отправляет прежний action (+1), дальнейший сценарий прежний. Кнопка
   не появляется вне прежних условий. При отсутствии локализованной строки
   или выключенном LoadAllLocales остаётся enUS, отсутствующий entry не вызывает crash.
8. Gilneas 14204/14159/14375: пройти существующие исправленные цепочки обоими
   языками, сравнить мастиффа/скрытней, появление Avery-worgen, оковы/transition.
   Локализация не является исправлением этих механик. Их поля и классификации
   перечислены в game-test-samples.json: даже неизменённый квест проверяется
   как контроль. Нет возможности выполнить — оставить «не проверено».

Выборочная проверка строк не доказывает прохождение всего контента. Для ручной
редактуры/новых переводов нужен отдельный пакет с before/after и семантическим
обоснованием; текущие существующие непустые тексты намеренно сохранены.
