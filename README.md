# 1KYCore

**Серверное ядро World of Warcraft: Legion 7.3.5 на C++.**

1KYCore — открытый проект на основе SylvaniaCore и DestinyCore, происходящих
из семейства TrinityCore. Основное направление разработки — исправление ошибок,
поддержка игрового контента и сохранение штатных механик игры.

[Скачать базу данных](https://github.com/sib-ouroboros/1KYCore/releases/tag/db735.02-r1) ·
[Все релизы](https://github.com/sib-ouroboros/1KYCore/releases) ·
[Сборки](https://github.com/sib-ouroboros/1KYCore/actions) ·
[Сообщить об ошибке](https://github.com/sib-ouroboros/1KYCore/issues)

## О проекте

В репозитории находятся исходный код серверов авторизации и игрового мира,
скрипты контента, инструменты извлечения клиентских данных и SQL-обновления.
Проект находится в разработке: успешная компиляция не означает, что весь
контент дополнения уже проверен в игре.

Текущая работа ведётся в ветке
[`cleanup/remove-bots`](https://github.com/sib-ouroboros/1KYCore/tree/cleanup/remove-bots).
Проверки компиляции выполняются для Windows x64, GCC и Clang через GitHub Actions.

## База данных

База доступна в [Releases 1KYCore](https://github.com/sib-ouroboros/1KYCore/releases/tag/db735.02-r1).

| Файл | Содержимое |
| --- | --- |
| [DB735.02.rar](https://github.com/sib-ouroboros/1KYCore/releases/download/db735.02-r1/DB735.02.rar) | Полные дампы `world` и `hotfixes`, около 84 МиБ |
| [1KYCore-database-support-a9ab2d665eac.zip](https://github.com/sib-ouroboros/1KYCore/releases/download/db735.02-r1/1KYCore-database-support-a9ab2d665eac.zip) | Схемы `auth`, `characters`, `shop`, SQL-обновления и инструкция на русском |
| [SHA256SUMS](https://github.com/sib-ouroboros/1KYCore/releases/download/db735.02-r1/SHA256SUMS) | Контрольные суммы файлов |
| [database-source.json](https://github.com/sib-ouroboros/1KYCore/releases/download/db735.02-r1/database-source.json) | Источник базы и точный коммит SQL-пакета |

Исходный архив взят из [DestinyCore DB735.02](https://github.com/slash-design/DestinyCore/releases/tag/DB735.02)
и размещён без изменений. Его размер и SHA-256 проверены. SQL-пакет соответствует
коммиту `a9ab2d665eac`; исполняемые файлы сервера в этот релиз не входят.
Импорт базы и совместимость с работающим сервером пока не проверены.

Порядок установки описан в `docs/database-release.md` внутри ZIP. Для новой
установки нужны оба архива. Полные дампы не предназначены для обновления
существующей базы с персонажами. Каталог `sql/base/dev` содержит пустые схемы
и не заменяет полноценные дампы `world` и `hotfixes`.

## Сборка

Для сборки нужны CMake 3.24 или новее, компилятор C++, Boost, OpenSSL и
клиентская библиотека MySQL. Точные версии зависимостей и команды, используемые
на проверочных машинах, находятся в
[workflow-файлах](https://github.com/sib-ouroboros/1KYCore/tree/cleanup/remove-bots/.github/workflows).

```bash
git clone --branch cleanup/remove-bots https://github.com/sib-ouroboros/1KYCore.git
cd 1KYCore
cmake -S . -B build -DTOOLS=ON
cmake --build build --parallel
```

На Windows выберите подходящий генератор CMake и установленный компилятор
Visual Studio. Размещение готовых файлов зависит от выбранного генератора
и конфигурации сборки.

Для запуска также потребуются данные, извлечённые из совместимого клиента
Legion 7.3.5, установленные базы и настроенные файлы конфигурации `bnetserver`
и `worldserver`. Образцы конфигурации находятся рядом с соответствующими
исходниками серверов. Параметры подключения к MySQL задаются для вашей установки.

Некоторые внутренние имена и цели сборки сохраняют названия исходного проекта
для совместимости с существующими инструментами.

## Участие в разработке

Для сообщения об ошибке создайте [issue](https://github.com/sib-ouroboros/1KYCore/issues).
Укажите коммит ядра, версию базы, шаги воспроизведения, ожидаемое поведение
и соответствующий фрагмент журнала без паролей и других секретов.

Изменения кода и документации можно предложить через pull request. Указывайте,
что исправлено и как проверялось изменение.

## Благодарности и лицензия

Проект использует результаты работы [SylvaniaCore](https://github.com/BlaMacfly/SylvaniaCore),
[DestinyCore](https://github.com/slash-design/DestinyCore) и
[TrinityCore](https://github.com/TrinityCore/TrinityCore). Авторство исходного кода
и лицензионные уведомления сохранены.

Условия распространения приведены в [COPYING](COPYING).

World of Warcraft и Blizzard Entertainment — товарные знаки соответствующих
правообладателей. Проект не связан с Blizzard Entertainment.
