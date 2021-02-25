from django.urls import path
from .views import UserProfileCreateView, UserProfileRUDView, GetOrCreateUserProfile, BookRetrieveView, BookListView, \
    BasketCreateView

urlpatterns = [
    # user profile
    path('user_profile/create/', UserProfileCreateView.as_view()),
    path('user_profile/<int:user_profile_id>/', UserProfileRUDView.as_view()),
    path('user_profile/<phone_number>/get_or_create/', GetOrCreateUserProfile.as_view()),


    # book
    path('book/<int:book_id>/', BookRetrieveView.as_view()),
    path('book/list/', BookListView.as_view()),

    # basket
    path('basket/create/', BasketCreateView.as_view()),
]