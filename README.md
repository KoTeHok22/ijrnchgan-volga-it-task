# Выполнил Мишин Вадим

Запустить на Linux не смог :(
Выдает ошибку "Unsupported config", хотя на Windows все запускается.

# Запуск:
Перейти в директорию проекта
Выполнить команду "docker-compose up -d" 
По адресу http://localhost:5000/ должна появиться надпись YES
Вы великолепны!

# Аккаунты по умолчанию:
Логин   | Пароль  | Роль
user    | user    | user
doctor  | doctor  | doctor
manager | manager | manager
admin   | admin   | admin

# Доступные адреса:
http://localhost:5000/SignIn - Вход в аккаунт
http://localhost:5000/SignUp - Регистрация аккаунта
http://localhost:5000/profile - Профиль аккаунта
http://localhost:5000/profile/settings - Настройка аккаунта
http://localhost:5000/profile/accounts - Вывод всех пользователей, настройка пользователя, поиск пользователя, удаление пользователя
Для остального страницы реализовать не успел, но все API по заданию были реализованы

# Документация Swagger:

[Микросервис Аккаунтов](https://app.swaggerhub.com/apis/KOTENOK210903_1/accounts-api-Volga-IT/1.0.0)
[Микросервис Больниц](https://app.swaggerhub.com/apis/KOTENOK210903_1/hospitals-api-Volga-IT/1.0.0)
[Микросервис Расписания](https://app.swaggerhub.com/apis/KOTENOK210903_1/timetable-api-Volga-IT/1.0.0)
[Микросервис Документов](https://app.swaggerhub.com/apis/KOTENOK210903_1/documents-api-Volga-IT/1.0.0)