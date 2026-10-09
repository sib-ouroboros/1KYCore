# Воспроизведение чистого старта и shutdown на Linux

Статус: инструкция и инструменты подготовлены; полный тест ещё не выполнен.
`startup-audit.yml` собирает Dynamic RelWithDebInfo и отдельный ASan/UBSan вариант.
`--version` в CI — только проверка бинарника, не проверка shutdown.

## Изоляция

Использовать отдельный Linux стенд. Не копировать рабочий конфиг без изменения всех
пяти подключений и портов. Создать новые базы `1kycore_audit_auth`,
`1kycore_audit_world`, `1kycore_audit_characters`, `1kycore_audit_hotfixes`,
`1kycore_audit_shop`; отдельному MySQL-пользователю дать доступ только к ним.
Пароль хранить в файле конфигурации с правами 0600, не передавать в командной строке.
Оставить World/Hotfix пустыми для штатного auto-population. Auth/Characters/Shop
инициализировать соответствующими файлами из `sql/base`, указав аудит-базы.
Добавить в audit auth realmlist отдельный realm с build 26972 и локальными адресами.
Нельзя импортировать `sql/base/dev` вместо release base.

Сохранить SHA256 release `DB_world_735.02.sql`, `DB_hotfixes_735.02.sql`, точный commit,
SQL update ledger и SHA256 используемых maps/vmaps/mmaps/dbc. Данные клиента должны
соответствовать 26972; имеющиеся локальные 26654 не являются доказательством совместимости.
Проверить пустоту World/Hotfix через information_schema до первого запуска и сохранить
вывод. Probe сам не создаёт/не сбрасывает базы и не удостоверяет их исходную пустоту.

В самостоятельном `audit.conf` явно задать:

```ini
LoginDatabaseInfo = "127.0.0.1;3306;audit_user;PASSWORD;1kycore_audit_auth"
WorldDatabaseInfo = "127.0.0.1;3306;audit_user;PASSWORD;1kycore_audit_world"
CharacterDatabaseInfo = "127.0.0.1;3306;audit_user;PASSWORD;1kycore_audit_characters"
HotfixDatabaseInfo = "127.0.0.1;3306;audit_user;PASSWORD;1kycore_audit_hotfixes"
ShopDatabaseInfo = "127.0.0.1;3306;audit_user;PASSWORD;1kycore_audit_shop"
RealmID = 1
BindIP = "127.0.0.1"
WorldServerPort = 18085
InstanceServerPort = 18086
Console.Enable = 1
Ra.Enable = 0
SOAP.Enabled = 0
WorldREST.Enabled = 0
Updates.EnableDatabases = 31
Updates.AutoSetup = 1
SourceDirectory = "/path/to/exact-checkout"
DataDir = "/path/to/26972-data"
```

Остальные параметры брать из конфигурации этого checkout. Проверить SourceDirectory,
SQL include paths и audit auth realm; не удалять SQL update ledger ради повторного теста.
Probe отклоняет секции/includes, дубликаты ключей, нелокальные БД, общие имена и обычные порты.
Это защита от случайного запуска на production, не замена отдельному DB пользователю.

## Сборки

Публикация изменений audit-инструментов в feature-ветку автоматически запускает обе сборки.
После появления workflow в default branch также доступен ручной запуск
`Clean startup audit preparation` с `build_diagnostics=true`.
Два артефакта содержат бинарники и Dynamic modules одного commit. Использовать отдельные
каталоги установки. Sanitizer-сборка: `-O1 -g -fno-omit-frame-pointer
-fsanitize=address,undefined`, jemalloc отключён. RelWithDebInfo для GDB собран отдельно.
CI использует Ubuntu 22.04; версия библиотек отличается от исходного Linux лога
(Boost 1.83/OpenSSL 3.0.13). Для окончательного диагноза нужен также GDB исходного бинарника
или воспроизведение с теми же библиотеками. Сохранять unstripped binaries и modules.

## Запуск и автоматический shutdown

```bash
python3 contrib/tools/worldserver_bootstrap_probe.py \
  --server /audit/asan/bin/worldserver --config /audit/asan/audit.conf \
  --output-dir /audit/results/asan
```

Probe ждёт ready, отправляет `server shutdown 1`, проверяет exit code и запускает
анализатор лога. Ошибка, незавершённый startup, timeout, ASan/UBSan или неожиданные
loader сообщения возвращают ненулевой код. ASAN_OPTIONS/UBSAN_OPTIONS устанавливаются
без suppression-файлов. По умолчанию legacy allowlist пуст; PASS не ожидается,
пока реальные P0/P1 не устранены, а P2/P3 не разобраны.

Для независимого полного bootstrap второй сборки использовать новый комплект audit-баз
с другими суффиксами; повторный запуск существующих баз проверяет shutdown, а не чистый импорт.

```bash
python3 contrib/tools/worldserver_bootstrap_probe.py \
  --server /audit/rel/bin/worldserver --config /audit/rel/audit.conf \
  --output-dir /audit/results/gdb --gdb
```

GDB выполняет `run` и `thread apply all bt full`. Весь stdout/stderr сохраняется
в `worldserver.log`. Для существующего core использовать соответствующие unstripped
worldserver и .so, сохранив исходные пути библиотек либо настроив GDB sysroot/solib-search-path:

```bash
gdb -batch -ex 'set pagination off' -ex 'thread apply all bt full' \
  /path/to/matching/worldserver /path/to/core > /audit/results/core-backtrace.txt 2>&1
```

Core dump может содержать персональные данные/секреты. Для первичного расследования
достаточна трассировка с точными символами и версиями модулей; не публиковать core в Git.

## Проверка лога и бюджета

```bash
python3 contrib/tools/worldserver_log_audit.py /audit/results/asan/worldserver.log \
  --json /audit/results/asan/review.json --exit-code 0 --fail-on-integrity
```

`--exit-code` обязан быть фактическим кодом завершения, не предполагаемым нулём.
Предпочтительно пользоваться автоматическим probe, который получает его от процесса.
Allowlist — JSON-массив `{ "line_sha256": "...", "reason": "..." }`, только для
точной строки P2/P3 с объяснением. Regex/маски и исключения P0/P1 отвергаются.
Allowlist не означает FIXED. Пустая optional таблица получает P3 до явного обоснования;
mysql CLI warning и отсутствие имён персонажей в свежей базе выделяются как INFO_NOISE.

Для завершения ТЗ нужны: clean import evidence, update ledger, готовность сервера,
нормальный exit, чистая sanitizer-трассировка, GDB-доказательство исправленного P0,
проверка зависимостей и сравнение before/after. `audit.json` probe содержит
`empty_database_bootstrap_verified=false`, пока исходная пустота не подтверждена отдельным
протоколом; отдельный PASS анализатора не означает завершение всего ТЗ.
