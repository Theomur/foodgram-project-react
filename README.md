# Проект «Фудграм»

### Описание

Сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

#### Технологии использованные в проекте  :

* Python (V3.9.10)
* Django
* DRF
* Nginx
* Gunicorn
* Docker
* Workflow

### Как запустить проект:

Клонировать репозиторий

Заполнить *.env* файл в соответствии с *.env.example*, например:
```
SECRET_KEY=django-insecure-1234567890
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost,yandex-project.com
SQLITE_DB=False

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

DB_HOST=db
DB_PORT=5432
DB_NAME=postgres
```

Собрать контейнеры:
```
cd foodgram-project-react/infra
sudo docker compose up -d
```

Сделать миграции, собрать статику и создать суперпользователя:
```
sudo docker compose exec -T backend python manage.py makemigrations users
sudo docker compose exec -T backend python manage.py makemigrations recipes
sudo docker compose exec -T backend python manage.py migrate
sudo docker compose exec -T backend python manage.py collectstatic --no-input
```

Чтобы заполнить базу данных начальными данными списка ингридиетов выполните:
```
sudo docker compose exec -T backend python manage.py load_ingredients
```

Доступ к сайту:
http://158.160.76.235/

Доступ в админку:
http://158.160.76.235/admin

Данные для работы с админкой:
```
login: admin@mail.com
password: 0000
```

Автор: [Коновалов Антон](https://github.com/Theomur)