from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models


def validate_username(value):
    if value.lower() == "me":
        raise ValidationError('Имя пользователя "me" недопустимо.')


class User(AbstractUser):
    email = models.EmailField(unique=True,
                              max_length=settings.LINE_LIMIT_EMAIL)
    first_name = models.CharField(max_length=settings.LINE_LIMIT_USERS)
    last_name = models.CharField(max_length=settings.LINE_LIMIT_USERS)

    username = models.CharField(
        max_length=settings.LINE_LIMIT_USERS,
        unique=True,
        validators=[validate_username, UnicodeUsernameValidator()],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ('username',)
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

    class Meta:
        verbose_name = 'Подписка на авторов'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'
