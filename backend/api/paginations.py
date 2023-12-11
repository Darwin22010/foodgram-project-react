from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    page_size = settings.PAGE_SIZE
    max_page_size = 20
    page_size_query_param = 'limit'
