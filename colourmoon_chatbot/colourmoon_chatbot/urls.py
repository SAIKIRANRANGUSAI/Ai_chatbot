from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),       # Admin dashboard & login
    path('', include('chatbot.urls')),         # index.html + chatbot API
]
