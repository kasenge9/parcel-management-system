from django.urls import path
from . import views
urlpatterns = [
    path("", views.home, name="home"), path("track/", views.track_parcel, name="track"),
    path("dashboard/", views.dashboard, name="dashboard"), path("parcels/", views.parcel_list, name="parcel_list"),
    path("parcels/new/", views.parcel_create, name="parcel_create"), path("parcels/<int:pk>/", views.parcel_detail, name="parcel_detail"),
    path("parcels/<int:pk>/status/", views.update_status, name="update_status"),
]
