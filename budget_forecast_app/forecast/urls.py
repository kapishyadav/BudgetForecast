from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('api/forecast/', views.forecast_api, name='forecast_api'),
    path("download_csv/<str:filename>/", views.download_forecast_csv, name="download_csv"),
]
