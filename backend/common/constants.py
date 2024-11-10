# Папки для загрузки изображений
AVATAR_UPLOAD_FOLDER = 'profile_pictures/'
RECIPE_IMAGE_UPLOAD_FOLDER = 'recipe_images/'

# Регулярные выражения и максимальные длины полей
REGEX = r'^[\w.@+-]+$'
EMAIL_MAX_LENGTH = 254
NAME_MAX_LENGTH = 150
RECIPE_NAME_MAX_LENGTH = 256
SHORT_CODE_MAX_LENGTH = 5
DEFAULT_MAX_LENGTH = 75

# Сообщения об ошибках
ERROR_INVALID_USERNAME = (
    'Имя пользователя должно содержать только буквы, цифры и .@+-')
ERROR_EMPTY_INGREDIENTS = 'Рецепт должен содержать хотя бы один ингредиент.'
ERROR_DUPLICATE_INGREDIENTS = 'Ингредиенты не должны повторяться.'
ERROR_EMPTY_TAGS = 'Рецепт должен содержать хотя бы один тег.'
ERROR_DUPLICATE_TAGS = 'Теги не должны повторяться.'
ERROR_MISSING_INGREDIENTS_FIELD = (
    'Поле "ingredients" обязательно для заполнения.')
ERROR_MISSING_TAGS_FIELD = 'Поле "tags" обязательно для заполнения.'

ERROR_CANNOT_SUBSCRIBE_TO_SELF = 'Вы не можете подписаться на себя.'
ERROR_ALREADY_SUBSCRIBED = 'Вы уже подписаны на этого пользователя.'
ERROR_SUBSCRIPTION_NOT_FOUND = 'Подписка не найдена.'

ERROR_NOT_AUTHENTICATED = 'Вы должны быть авторизованы, чтобы создать рецепт.'
ERROR_RECIPE_ALREADY_ADDED = 'Рецепт уже добавлен.'
ERROR_RECIPE_NOT_FOUND = 'Рецепт не найден в списке.'
ERROR_CART_EMPTY = 'Ваша корзина пуста.'

# URL пути для разных действий
URL_SUBSCRIBE_PATH = 'subscribe'
URL_SUBSCRIPTIONS_PATH = 'subscriptions'
URL_CURRENT_USER_PATH = 'me'
URL_AVATAR_PATH = 'me/avatar'
RECIPES_URL_PATH = 'recipes'
SHORT_URL_PATH = 's'

URL_FAVORITES_PATH = 'favorite'
URL_SHOPPING_CART_PATH = 'shopping_cart'
URL_DOWNLOAD_SHOPPING_CART_PATH = 'download_shopping_cart'
URL_GET_LINK_PATH = 'get-link'

SHOPPING_CART_FILENAME = 'shopping_cart.txt'
