from django.urls import path
from api.views import conversation

urlpatterns = [
    path("conversation", conversation),
    path("conversation/", conversation),
]
