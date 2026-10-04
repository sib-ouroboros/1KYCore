# Предлагаемое описание ревью

## Заголовок

Добавить проверенные ruRU SQL-пакеты и локаль сессии в меню Аргуса

## Результат

От development/character-tools `567027437455e56d8d055a56a064b462921b49c8`
подготовлена отдельная feature/ruRU-localization без push/merge/production.
Добавлены все 62 656 подтверждённых по английскому исходнику и назначению
текстовых полей allowlist: 22 565 world и 40 091 BroadcastText/hotfixes.
Непустые прежние переводы, enUS, другие локали, базовые игровые сущности и
механика сохранены. 525 небольших optional-пакетов с guarded exact rollback,
источниками, hashes и читаемыми proposals упакованы детерминированным gzip
(суммарно около 34 MB); большие исходные дампы/полные rejected reports вне Git.

В меню Велена 120977 существующий BroadcastText 27602 выбирается по session
locale/gender с enUS fallback. Исправлена маска DB2, ранее исключавшая ruRU
при загрузке дополнительных локализованных файлов. При all-files disabled
не объявляются не загруженные локали; LOCALE_none исключена.

Инструменты анализируют дампы read-only, проверяют SHA/schema/PK/UTF8, сравнивают
конкретные поля, защищают токены, printf/links и экспорт CSV. SQL CAS отказывается
от устаревшей цели до постоянных записей; новые строки откатываются только при
полной принадлежности пакету. Пакеты исключены из штатного startup updater.

## Проверка

Все world/hotfix пакеты на prepared release + current migrations MySQL8.0.45:
apply/reapply/stale apply/stale rollback/full rollback/repeated rollback/partial
retry PASS. Сравнены все 248 world и 368 hotfix таблиц и полные locale rows.
MyISAM/InnoDB synthetic NULL/empty/collation/ownership/later edit guards PASS.
23 Python unit test и изолированная C++ компиляция действительных helper/native
fallback/mask PASS (Windows GCC16.2, без sanitizers).

Повторная генерация через public CLI и проверка/extraction всех gzip/SQL hashes
описаны в validation; bundle работает без доступа к базе. Контрольные суммы
baseline/restored и реальное покрытие по полям сохранены для ревью.

## Пределы и очередь

Полная сборка сервера, тестовый startup и клиентская приёмка не выполнены:
в среде нет полного server toolchain/запущенной тестовой игры. Это обязательные
следующие приёмочные проверки по validation.ru.md; не выдаём их за успешные.
Тест MySQL8 не подтверждает точную MariaDB-версию deployment.
Не заявлено 100%: mismatch/foreign locale/unknown binding/invalid source и
непустые существующие переводы сохранены в очередях. Для pointer import 0
подтверждений, у CreatureText нет соответствующего locale-донорского источника,
прочие DB2/hotfix families требуют отдельного semantic matching.
365 эвристических C++ visible-call sites остаются manual, не массовая замена.
Происхождение/лицензирование источника отдельно зафиксировано в sources.json.
