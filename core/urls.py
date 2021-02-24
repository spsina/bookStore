from django.urls import path
from .views import UserProfileCreateView, UserProfileRUDView

urlpatterns = [
    path('user_profile/create/', UserProfileCreateView.as_view()),
    path('user_profile/<int:user_profile_id>/', UserProfileRUDView.as_view()),
]