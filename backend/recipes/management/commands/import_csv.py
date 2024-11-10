import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=os.path.join(settings.BASE_DIR, '../data/ingredients.csv'),
            help='Путь к CSV-файлу с ингредиентами.',
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs['file']
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)

                for row in reader:
                    name, measurement_unit = row[0], row[1]
                    Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit
                    )

            self.stdout.write(self.style.SUCCESS(
                'Ингредиенты успешно импортированы из CSV.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Произошла ошибка: {str(e)}'))
