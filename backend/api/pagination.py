from rest_framework.pagination import PageNumberPagination


class CommonPagination(PageNumberPagination):
    """
    Пагинация с фиксированным размером страницы
    и возможностью задать лимит через параметр запроса "limit".
    """
    page_size = 6
    page_size_query_param = 'limit'
