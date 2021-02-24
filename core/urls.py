from django.urls import path
from .views import UserProfileCreateView, UserProfileRUDView, GetOrCreateUserProfile

urlpatterns = [
    path('user_profile/create/', UserProfileCreateView.as_view()),
    path('user_profile/<int:user_profile_id>/', UserProfileRUDView.as_view()),
    path('user_profile/<phone_number>/get_or_create/', GetOrCreateUserProfile.as_view()),
]