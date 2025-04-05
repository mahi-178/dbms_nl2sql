from django.contrib import admin
from .models import Query, QueryFeedback

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'natural_language', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('natural_language', 'sql_query')
    readonly_fields = ('created_at',)

@admin.register(QueryFeedback)
class QueryFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'query', 'rating', 'is_helpful', 'created_at')
    list_filter = ('rating', 'is_helpful', 'created_at')
    search_fields = ('comments',)
    readonly_fields = ('created_at',)