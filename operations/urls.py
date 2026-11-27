from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("track/", views.track_parcel, name="track"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("parcels/", views.parcel_list, name="parcel_list"),
    path("parcels/new/", views.parcel_create, name="parcel_create"),
    path("parcels/<int:pk>/", views.parcel_detail, name="parcel_detail"),
    path("parcels/<int:pk>/status/", views.update_status, name="update_status"),
    path("staff/users/", views.staff_users, name="staff_users"),
    path("staff/users/new/", views.staff_user_create, name="staff_user_create"),
]
