from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator, RegexValidator
from django.db import models

from common.constants import (AVATAR_UPLOAD_FOLDER, EMAIL_MAX_LENGTH,
                              ERROR_INVALID_USERNAME, NAME_MAX_LENGTH, REGEX)


class FoodgramUser(AbstractUser):
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True, blank=False, null=False,
        validators=[EmailValidator()],
        verbose_name='Адрес электронной почты',)
    username = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True, blank=False, null=False,
        validators=[RegexValidator(
            regex=REGEX,
            message=ERROR_INVALID_USERNAME)],
        verbose_name='Имя пользователя')
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH, blank=False, null=False,
        verbose_name='Имя')
    last_name = models.CharField(
        max_length=NAME_MAX_LENGTH, blank=False, null=False,
        verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to=AVATAR_UPLOAD_FOLDER, blank=True, null=True,
        verbose_name='Фото')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Пользователь')
    subscribed_to = models.ForeignKey(
        FoodgramUser,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Подписан на')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_to'], name='unique_subscription')
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.subscribed_to}'
