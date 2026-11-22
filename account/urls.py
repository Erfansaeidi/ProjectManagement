# account/urls.py
from django.urls import path
from .views import *

urlpatterns = [

    path("signup/", SignUpView.as_view(), name="signup"),
    path("home/", HomeView.as_view(), name="home"),

]