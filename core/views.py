import json

import furl
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView

from BookStore.settings import DEBUG
from .serializers import UserProfileSerializer, BookSerializer, BasketCreate, SendCodeSerializer, GetUserInfoSerializer, \
    InvoiceDetailedSerializer, ConfigSerializer
from .models import UserProfile, Book, Invoice, UserProfilePhoneVerification, Config
from .permissions import IsLoggedIn
from django.utils.translation import gettext as _

from .vandar import vandar_prepare_for_payment, vandar_verify_payment


class UserProfileSendCode(generics.CreateAPIView):
    serializer_class = SendCodeSerializer


class UserProfileRUView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsLoggedIn,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user.user_profile


class GetUserInfoView(generics.GenericAPIView):
    serializer_class = GetUserInfoSerializer

    def post(self, request, *args, **kwargs):
        serializer, user_profile = self.get_user_profile(request)
        vo = self.get_verification_object(user_profile)

        if not vo or not vo.is_usable:
            return Response({'phone_number': _("Phone number not found")}, status=400)

        if not self.is_code_correct(serializer, vo):
            return self.handle_wrong_code_and_return_response(vo)

        self.use_the_code(vo)
        return Response(UserProfileSerializer(instance=user_profile).data)

    def handle_wrong_code_and_return_response(self, vo):
        remaining_query_times = self.handle_wrong_code_and_get_remaining_query_times(vo)
        return Response({'code': _("Incorrect Code"), 'remaining_query_times': remaining_query_times}, status=400)

    @staticmethod
    def use_the_code(vo):
        vo.used = True
        vo.save()

    @staticmethod
    def is_code_correct(serializer, vo):
        return vo.code == serializer.validated_data.get('code')

    @staticmethod
    def get_verification_object(user_profile):
        vo = UserProfilePhoneVerification.objects.last_not_expired_verification_object(user_profile=user_profile)
        return vo

    @staticmethod
    def handle_wrong_code_and_get_remaining_query_times(vo):
        # todo: anti concurrency
        vo.query_times += 1
        GetUserInfoView.burn_the_vo_if_maxed_out(vo)
        vo.save()
        remaining_query_times = UserProfilePhoneVerification.MAX_QUERY - vo.query_times
        return remaining_query_times

    @staticmethod
    def burn_the_vo_if_maxed_out(vo):
        if vo.query_times == UserProfilePhoneVerification.MAX_QUERY:
            vo.burnt = True

    def get_user_profile(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_profile = get_object_or_404(UserProfile, phone_number=serializer.validated_data.get('phone_number'))
        return serializer, user_profile


class BookRetrieveView(generics.RetrieveAPIView):
    serializer_class = BookSerializer
    queryset = Book.objects.filter(is_delete=False)
    lookup_field = 'pk'
    lookup_url_kwarg = 'book_id'


class BookListView(generics.ListAPIView):
    serializer_class = BookSerializer
    queryset = Book.objects.filter(is_delete=False)

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['pk', ]


class BasketCreateView(generics.CreateAPIView):
    permission_classes = (IsLoggedIn,)
    serializer_class = BasketCreate

    def perform_create(self, serializer):
        serializer.save(user_profile=self.request.user.user_profile)


class MakePaymentView(APIView):

    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, internal_id=kwargs.get('internal_id'))

        # reject invalid basket
        if not invoice.basket.is_valid_for_payment:
            return Response({'details': _("Invalid Basket")}, status=400)

        result = vandar_prepare_for_payment(invoice, request)

        # vandar failed to create redirect url
        if result.get('status') != 200:
            return Response(result)

        # redirect url fetched from vandar
        return Response({
            'redirect_to': result.get('redirect_to')
        })


class VerifyPaymentView(APIView):

    @staticmethod
    def doesHaveValidBasket(invoice):
        basket = invoice.basket
        return basket.is_valid_for_verification

    @staticmethod
    def validateInvoice(invoice):
        if DEBUG:
            invoice.status = Invoice.PAYED
            invoice.save()
        else:
            vandar_verify_payment(invoice)

    @staticmethod
    def isInvoiceValidated(invoice):
        return invoice.status == Invoice.PAYED

    @staticmethod
    def getInvoiceSerializedData(invoice):
        return InvoiceDetailedSerializer(instance=invoice).data

    @staticmethod
    def get(request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, internal_id=kwargs.get('internal_id'))
        self = VerifyPaymentView

        if not self.doesHaveValidBasket(invoice):
            return Response(self.getInvoiceSerializedData(invoice), status=400)

        self.validateInvoice(invoice)

        if not self.isInvoiceValidated(invoice):
            return Response(self.getInvoiceSerializedData(invoice), status=400)

        return Response(self.getInvoiceSerializedData(invoice), status=200)


class VerifyPaymentAndRedirectView(APIView):

    @staticmethod
    def get(request, *args, **kwargs):
        verify_payment_view = VerifyPaymentView.get
        response = verify_payment_view(request, *args, **kwargs)
        url = furl.furl('https://abee.ir/store/invoice/')

        # print(response.data)
        url.args['response'] = json.dumps({
            'status_code': response.status_code,
            'data': response.data
        })

        return HttpResponseRedirect(redirect_to=url.url)


class GetConfigView(generics.RetrieveAPIView):
    serializer_class = ConfigSerializer

    def get_object(self):
        return Config.get_instance()
