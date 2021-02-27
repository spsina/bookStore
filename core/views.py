from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserProfileSerializer, BookSerializer, BasketCreate, SendCodeSerializer
from .models import UserProfile, Book, Invoice
from .permissions import IsLoggedIn
from django.utils.translation import gettext as _

from .vandar import vandar_prepare_for_payment


class UserProfileSendCode(generics.CreateAPIView):
    serializer_class = SendCodeSerializer


class BookRetrieveView(generics.RetrieveAPIView):
    serializer_class = BookSerializer
    queryset = Book.objects.filter(is_delete=False)
    lookup_field = 'pk'
    lookup_url_kwarg = 'book_id'


class BookListView(generics.ListAPIView):
    serializer_class = BookSerializer
    queryset = Book.objects.filter(is_delete=False)


class BasketCreateView(generics.CreateAPIView):
    permission_classes = (IsLoggedIn,)
    serializer_class = BasketCreate

    def perform_create(self, serializer):
        serializer.save(user_profile=self.request.user.user_profile)


class MakePaymentView(APIView):

    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, internal_id=kwargs.get('internal_id'))

        # reject invalid basket
        if not invoice.basket.is_valid:
            return Response({'details': _("Invalid Basket")}, status=400)

        result = vandar_prepare_for_payment(invoice, request)

        # vandar failed to create redirect url
        if result.get('status') != 200:
            return Response(result)

        # redirect url fetch from vandar
        return Response({
            'redirect_to': result.get('redirect_to')
        })
