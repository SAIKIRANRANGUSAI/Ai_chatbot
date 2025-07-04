from django.urls import path
from .views import chatbot_api, chatbot_home


urlpatterns = [
    path('', chatbot_home, name='chat_home'),
    path('api/chat/', chatbot_api, name='chatbot_api'),
]
