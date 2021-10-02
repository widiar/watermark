from django.urls import path
from .views import *

urlpatterns = [
    path('', HalamanDepanView.as_view()),
    path('read', ReadKTPView.as_view()),
    path('delete', deleteAfterClick)
]