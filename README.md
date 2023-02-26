# InEx: Initialize & Execute

## Установка через pip в текущее виртуальное окружение

```bash
pip install -U inex
```
или
```bash
pip install -U --index-url "https://nid-artifactory.ad.speechpro.com/artifactory/api/pypi/pypi/simple" inex
```
если `pip` не сконфигурирован для загрузки пакетов из [`https://nid-artifactory.ad.speechpro.com`](https://nid-artifactory.ad.speechpro.com).

Конфигурирование `pip` для работы с
[`https://nid-artifactory.ad.speechpro.com`](https://nid-artifactory.ad.speechpro.com)
описано [здесь](https://confluence.speechpro.com/x/kLCeCg).

```bash
# Если pip старый, то он не знает команды config, поэтому его надо обновить:
python -m pip install --upgrade pip
# Прописываем Artifactory
pip config set global.index-url "https://nid-artifactory.ad.speechpro.com/artifactory/api/pypi/pypi/simple"
```

## Установка для разработки в новое виртуальное окружение с запуском тестов

```bash
git clone https://nid-gitlab.ad.speechpro.com/asr2/inex.git
cd inex
./install.sh
```

## Установка для разработки в текущее виртуальное окружение

```bash
git clone https://nid-gitlab.ad.speechpro.com/asr2/inex.git
cd inex
pip install -e .
```

## Параметры командной строки

```text
inex -h
usage: inex [-h] [--version] [--log-level LOG_LEVEL] [--log-path LOG_PATH] [--sys-paths SYS_PATHS] [--merge MERGE] [--update UPDATE] config_path

InEx

positional arguments:
  config_path           path to the configuration file (in YAML or JSON) or string with configuration in YAML

options:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
  --log-level LOG_LEVEL, -l LOG_LEVEL
                        set the root logger level
  --log-path LOG_PATH, -g LOG_PATH
                        path to the log-file
  --sys-paths SYS_PATHS, -s SYS_PATHS
                        paths to add to the list of system paths (sys.path)
  --merge MERGE, -m MERGE
                        path to the configuration file to be merged with the main config
  --update UPDATE, -u UPDATE
                        update or set value for some parameter (use "dot" notation: "key1.key2=value")
```
