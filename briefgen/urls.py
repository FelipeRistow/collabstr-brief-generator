"""URL configuration for the AI Brief Generator.

Two routes only: the page and the JSON API.
"""

from django.urls import path

from generator import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/generate/", views.generate, name="generate"),
]
