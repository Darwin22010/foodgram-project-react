# praktikum_new_diplom
У меня возникли проблемы с запуском сайта на удаленном сервере, почему то мой бекэнд не запускается, а постоянно перезвапускается из за чего я не могу сделать миграции:
foodgram-backend-1   darwin22010/foodgram_backend   "gunicorn foodgram.wsgi:application --bind 0:8000"   backend   19 seconds ago   Restarting (3) 1 second ago
В логах пишет это: https://hastebin.com/share/monozakera.scss , не может найти модуль corsheaders, хотя в requirments я его закинул.
