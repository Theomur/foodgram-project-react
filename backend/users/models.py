from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models


def validate_username(value):
    # Проверка на использование "me" в качестве имени пользователя
    if value.lower() == "me":
        raise ValidationError('Имя пользователя "me" недопустимо.')


class User(AbstractUser):
    email = models.EmailField(
        max_length=settings.LENGTH_OF_FIELDS_USER_RELATED,
        unique=True
    )
    first_name = models.CharField(
        max_length=settings.LENGTH_OF_FIELDS_USER_RELATED,
        blank=False
    )
    last_name = models.CharField(
        max_length=settings.LENGTH_OF_FIELDS_USER_RELATED,
        blank=False
    )

    username = models.CharField(
        max_length=settings.LENGTH_OF_USERNAME,
        unique=True,
        validators=[validate_username, UnicodeUsernameValidator()],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

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

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'

    class Meta:
        verbose_name = 'Подписка на авторов'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscribe'
            )
        ]
