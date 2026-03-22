from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('home/', TemplateView.as_view(template_name='hello_vite.html'), name='home'),
    path('upload/', views.upload_file, name='upload_file'),
    path('trigger-forecast/', views.trigger_forecast, name='trigger_forecast'),
    path('api/forecast/', views.forecast_api, name='forecast_api'),
    path("download_csv/", views.download_forecast_csv, name="download_csv"),
    path("get_suggestions/", views.get_suggestions, name="get_suggestions"),
    path('status/<str:task_id>/', views.check_task_status, name='check_task_status'),
    path('api/dashboard-data/', views.get_dashboard_data, name='get_dashboard_data'),
    path('api/run-scenario/', views.run_custom_scenario, name='run_custom_scenario'),
]
