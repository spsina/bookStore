from django.urls import path
from .views import BookRetrieveView, BookListView, \
    BasketCreateView, MakePaymentView

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
    # path('user_profile/send-code/', name="send_code"),

    # book
    path('book/<int:book_id>/', BookRetrieveView.as_view(), name="book_detail"),
    path('book/list/', BookListView.as_view(), name="books_list"),

    # basket
    path('basket/create/', BasketCreateView.as_view(), name="basket_create"),

    # payment
    path('payment/make/<internal_id>/', MakePaymentView.as_view(), name="payment_make"),
    path('payment/verify/<internal_id>/', MakePaymentView.as_view(), name="payment_verify"),

    # docs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
