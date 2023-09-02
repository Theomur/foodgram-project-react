from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
import re


def validate_username(value):
    # Проверка на использование "me" в качестве имени пользователя
    if value.lower() == "me":
        raise ValidationError('Имя пользователя "me" недопустимо.')


username_validator = RegexValidator(
    regex=re.compile('^[\w.@+-]+$'),
    message='Имя пользователя может содержать буквы, цифры и символы @/./+/-/_',
    flags=0
)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)

    nickname = models.CharField(max_length=255)

    username = models.CharField(
        max_length=255,
        unique=True,
        validators=[validate_username, username_validator],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'nickname']

    class Meta:
        ordering = ('registration_date', 'last_name', 'first_name', 'id')
        verbose_name = 'Пользователь'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed'
    )

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'

    class Meta:
        verbose_name = 'Подписка на авторов'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe'
            )
        ]
