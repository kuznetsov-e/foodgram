import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    Кастомное поле для работы с изображениями в формате base64.
    При получении строки base64, которая представляет изображение,
    данное поле декодирует строку, сохраняет изображение как файл
    с уникальным именем и передает его в стандартное поле изображения
    Django REST framework.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            filename = f'{uuid.uuid4()}.{ext}'

            data = ContentFile(base64.b64decode(imgstr), name=filename)

        return super().to_internal_value(data)
