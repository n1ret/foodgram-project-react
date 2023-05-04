from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        'email адрес',
        unique=True,
        error_messages={
            'unique': "email уже зарегистрирован",
        },
    )
    username = models.TextField(
        'имя пользователя',
        unique=True,
        error_messages={
            'unique': "такое имя уже используется",
        },
    )
    subscribers = models.ManyToManyField(
        'self', related_name='subscriptions', symmetrical=False
    )
    groups = None
    last_login = None

    class Meta:
        ordering = ['id']
