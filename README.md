# Проект «Фудграм»

### Описание

Сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

#### Технологии использованные в проекте  :

* Python
* Django
* DRF
* Nginx
* Gunicorn
* Docker
* Workflow

### Как запустить проект:

Клонировать репозиторий и перейти в папку backend в командной строке:

```
git clone git@github.com:/Theomur/foodgram-project-react

```
cd foodgram-project-react/backend
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

Доступ к сайту:
http://158.160.76.235/

Доступ в админку:
http://158.160.76.235/admin
```
login: admin@mail.com
password: 0000
```

Автор: Коновалов Антон