from django.contrib.auth.models import AbstractUser
from django.db import models


class FoodgramUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)
    username = models.CharField(
        max_length=150, unique=True, blank=False, null=False)
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=30, blank=False, null=False)
    avatar = models.ImageField(
        upload_to='profile_pictures/', blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        FoodgramUser, related_name='subscriptions', on_delete=models.CASCADE)
    subscribed_to = models.ForeignKey(
        FoodgramUser, related_name='subscribers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'subscribed_to')
