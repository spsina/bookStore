from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserProfileSerializer, BookSerializer, BasketCreate, SendCodeSerializer, GetUserInfoSerializer
from .models import UserProfile, Book, Invoice, UserProfilePhoneVerification
from .permissions import IsLoggedIn
from django.utils.translation import gettext as _

from .vandar import vandar_prepare_for_payment


class UserProfileSendCode(generics.CreateAPIView):
    serializer_class = SendCodeSerializer


class GetUserInfoView(generics.GenericAPIView):
    serializer_class = GetUserInfoSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_profile = get_object_or_404(UserProfile, phone_number=serializer.validated_data.get('phone_number'))
        vo = UserProfilePhoneVerification.objects.last_not_expired_verification_object(user_profile=user_profile)

        if not vo:
            return Response({'phone_number':  _("Phone number not found")}, status=400)

        if vo.is_usable:
            if vo.code == serializer.validated_data.get('code'):
                vo.used = True
                vo.save()
                return Response(UserProfileSerializer(instance=user_profile).data)

            # todo: anti concurrency
            vo.query_times += 1
            if vo.query_times == UserProfilePhoneVerification.MAX_QUERY:
                vo.burnt = True
            vo.save()
            remaining_query_times = UserProfilePhoneVerification.MAX_QUERY - vo.query_times
            return Response({'code': _("Incorrect Code"), 'remaining_query_times': remaining_query_times}, status=400)


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
