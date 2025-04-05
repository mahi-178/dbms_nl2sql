from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.contrib import admin
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('query/', views.query_view, name='query'),
    # path('query-page/', views.query_page, name='query-page'),
    path('process-query/', views.process_query, name='process_query'),
    path('history/', views.history_view, name='history'),
    path('feedback/<int:query_id>/', views.save_feedback, name='save_feedback'),
    path('export-csv/<int:query_id/', views.export_csv, name='export_csv'),
    path('rerun-query//', views.rerun_query, name='rerun_query'),
]