from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Register the ViewSet
# This automatically generates routes like:
# GET /cloud-integrations/ (List)
# POST /cloud-integrations/ (Create)
# GET /cloud-integrations/{id}/ (Retrieve)
# PATCH /cloud-integrations/{id}/ (Update)
# POST /cloud-integrations/{id}/sync-now/ (custom sync action!)
router.register(r'cloud-integrations', views.CloudIntegrationViewSet, basename='cloudintegration')

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
    path('api/visualize_history/', views.visualize_history, name='visualize_history'),
    # Add the Router URLs to the urlpatterns
    # By nesting it under 'api/', the final path becomes /api/cloud-integrations/
    path('api/', include(router.urls)),
]