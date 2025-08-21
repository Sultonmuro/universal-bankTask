from django.urls import path
from .views import rpc_handler

urlpatterns = [
    path("rpc/", rpc_handler, name="rpc_handler"),
]