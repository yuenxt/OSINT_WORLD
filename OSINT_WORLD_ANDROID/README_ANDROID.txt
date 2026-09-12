OSINT WORLD — Android

Это отдельная Android-версия игры. Она не использует Tkinter.
В проекте есть:
- регистрация/вход
- мобильный рабочий экран
- задания каждые 30 секунд
- цель задания и этапы поиска/сноса
- чат
- профиль
- магазин и инвентарь
- игровая анонимность
- Admin Center для выдачи номера/валюты
- SQLite

ВАЖНО:
Все данные поиска и сноса — синтетические и существуют только внутри игры.

СБОРКА APK НА WINDOWS:
1. Установи WSL2 (Ubuntu) в Windows.
2. В Ubuntu установи Python, pip, git и Buildozer:
   sudo apt update
   sudo apt install -y python3-pip python3-venv git zip unzip openjdk-17-jdk
   python3 -m pip install --user buildozer cython
3. Скопируй папку OSINT_WORLD_ANDROID в Linux/WSL.
4. Внутри папки:
   buildozer android debug
5. APK появится в папке bin.

Для первого запуска сборка может занять много времени, потому что скачивается Android toolchain.
