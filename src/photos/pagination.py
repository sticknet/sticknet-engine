from rest_framework import pagination

class DynamicPagination(pagination.PageNumberPagination):
	page_size_query_param = 'limit'
	max_page_size = 1000