from django.urls import path
from .views import BookRetrieveView, BookListView, \
    BasketCreateView, MakePaymentView, UserProfileSendCode, GetUserInfoView, UserProfileRUView, VerifyPaymentView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="BookStore API",
        default_version='v1',
        description="Abee Online Book Store",
        contact=openapi.Contact(email="snparvizi75@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # user profile
    path('user-profile/send/code/', UserProfileSendCode.as_view(), name="send_code"),
    path('user-profile/get/info/', GetUserInfoView.as_view(), name="get_user_info"),
    path('user-profile/', UserProfileRUView.as_view(), name="user_profile_retrieve_update"),


    # book
    path('book/<int:book_id>/', BookRetrieveView.as_view(), name="book_detail"),
    path('book/list/', BookListView.as_view(), name="books_list"),

    # basket
    path('basket/create/', BasketCreateView.as_view(), name="basket_create"),

    # payment
    path('payment/make/<internal_id>/', MakePaymentView.as_view(), name="payment_make"),
    path('payment/verify/<internal_id>/', VerifyPaymentView.as_view(), name="payment_verify"),

    # docs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
