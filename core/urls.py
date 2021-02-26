from django.urls import path
from .views import UserProfileCreateView, UserProfileRUDView, GetOrCreateUserProfile, BookRetrieveView, BookListView, \
    BasketCreateView, MakePaymentView

urlpatterns = [
    # user profile
    path('user_profile/create/', UserProfileCreateView.as_view()),
    path('user_profile/<int:user_profile_id>/', UserProfileRUDView.as_view()),
    path('user_profile/<phone_number>/get_or_create/', GetOrCreateUserProfile.as_view()),


    # book
    path('book/<int:book_id>/', BookRetrieveView.as_view(), name="book_detail"),
    path('book/list/', BookListView.as_view(), name="books_list"),

    # basket
    path('basket/create/', BasketCreateView.as_view(), name="basket_create"),

    # payment
    path('payment/make/<internal_id>/', MakePaymentView.as_view(), name="payment_make"),
    path('payment/verify/<internal_id>/', MakePaymentView.as_view(), name="payment_verify"),
]