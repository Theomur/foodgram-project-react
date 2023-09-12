from rest_framework.pagination import PageNumberPagination


class PageSizeControlPagination(PageNumberPagination):
    page_size_query_param = 'limit'
