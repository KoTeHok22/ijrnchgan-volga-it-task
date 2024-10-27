# Выполнил Мишин Вадим  
  
Запустить на Linux не смог :(  
Выдает ошибку "Unsupported config", хотя на Windows все запускается.  
  
# Запуск:  
Перейти в директорию проекта  
Переименовать файл "env" в ".env"  
Выполнить команду "docker-compose up -d"   
По адресу http://localhost:5000/ должна появиться надпись YES  
Вы великолепны!

# Доступ по API:  
Для доступа по API нужно в header указать 'X-Requested-With': 'XMLHttpRequest',  
А для доступа на защищенные адреса в cookies нужно указать access_token
```python
cookies = {
    'access_token': 'token',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
}
```  
  
Вечный токен с админским доступом (При условии, что секретный ключ не был изменен в .env):  
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3MjkxMDc5NDUsInN1YiI6NCwidHlwZSI6InBlcm1hbmVudF9hY2Nlc3MifQ.Hv-LThx114PGzJhXWjeuzNpR6IAqv2eGQzPHKh0lTzQ
```  


# Аккаунты по умолчанию:
<pre>
Логин   | Пароль   | Роль
--------|----------|-------
user    | user     | user
doctor  | doctor   | doctor
manager | manager  | manager
admin   | admin    | admin
</pre>
  
# Доступные адреса:  
http://localhost:5000/SignIn - Вход в аккаунт  
http://localhost:5000/SignUp - Регистрация аккаунта  
http://localhost:5000/profile - Профиль аккаунта  
http://localhost:5000/profile/settings - Настройка аккаунта  
http://localhost:5000/profile/accounts - Вывод всех пользователей, настройка пользователя, поиск пользователя, удаление пользователя, создание нового пользователя  
Для остального страницы реализовать не успел, но все API по заданию были реализованы  
  
# Документация Swagger:  
  
[Микросервис Аккаунтов](https://app.swaggerhub.com/apis/KOTENOK210903_1/accounts-api-Volga-IT/1.0.0)  
[Микросервис Больниц](https://app.swaggerhub.com/apis/KOTENOK210903_1/hospitals-api-Volga-IT/1.0.0)  
[Микросервис Расписания](https://app.swaggerhub.com/apis/KOTENOK210903_1/timetable-api-Volga-IT/1.0.0)  
[Микросервис Документов](https://app.swaggerhub.com/apis/KOTENOK210903_1/documents-api-Volga-IT/1.0.0)  
