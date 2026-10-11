# Базы 1KYCore с готовой ruRU-локализацией

Релиз [db735.02-ruru-20261011-r1](https://github.com/sib-ouroboros/1KYCore/releases/tag/db735.02-ruru-20261011-r1) содержит предоставленные владельцем
дампы MySQL от 11 октября 2026: DB_world_735.02.sql и DB_hotfixes_735.02.sql.
Файлы опубликованы в gzip без изменения SQL, вместе с SHA256SUMS и
database-source.json: размеры, хеши исходников и архивов, результаты проверки.
Бинарники сервера поставляются отдельно. Это снимок БД, а не миграция.

## Установка в пустые базы

Скачайте оба .sql.gz, SHA256SUMS и database-source.json из Releases.
В каталоге загрузки:

```bash
sha256sum -c SHA256SUMS
gzip -dk DB_world_735.02.sql.gz DB_hotfixes_735.02.sql.gz
mysql -u root -p -e "CREATE DATABASE world CHARACTER SET utf8mb4; CREATE DATABASE hotfixes CHARACTER SET utf8mb4;"
mysql --default-character-set=utf8mb4 -u root -p world < DB_world_735.02.sql
mysql --default-character-set=utf8mb4 -u root -p hotfixes < DB_hotfixes_735.02.sql
```

Пользователь MySQL и пароли должны соответствовать вашим настройкам.
Дампы не задают USE/CREATE DATABASE; целевая БД выбирается аргументом mysql.
Для auth/characters/shop используйте штатные схемы проекта только при новой
установке. Полные дампы содержат DROP TABLE — не импортируйте их в рабочие
world/hotfixes без намерения заменить данные и резервной копии.

Переводы ruRU уже включены. Автоматические папки ruRU удалены из текущей ветки;
повторное применение optional-пакетов не требуется. Остальные обновления
применяются штатным updater при запуске сервера с актуальным каталогом sql.
Снимок содержит журнал ранее применённых обновлений: после удаления файлов
локализации updater может сообщать об отсутствующих исторических SQL.
Это не отсутствие переводов; не очищайте весь журнал updates.

Полная проверка worldserver и клиентского прохождения не заменяется проверкой
импорта MySQL. Рабочий сервер при подготовке релиза не обновлялся.
