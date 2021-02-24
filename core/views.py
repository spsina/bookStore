from django.shortcuts import render
from rest_framework import generics
from .serializers import UserProfileSerializer
from .models import UserProfile
from .permissions import IsLoggedIn

class UserProfileCreateView(generics.CreateAPIView):
    serializer_class = UserProfileSerializer


class UserProfileRUDView(generics.RetrieveUpdateAPIView):

    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()
    permission_classes = (IsLoggedIn, )

    lookup_field = 'pk'
    lookup_url_kwarg = 'user_profile_id'


class GetOrCreateUserProfile(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        try:
            user_profile = UserProfile.objects.get(phone_number=self.kwargs.get('phone_number'))
            return user_profile
        except UserProfile.DoesNotExist:
            serializer = UserProfileSerializer(data={
                'phone_number': self.kwargs.get('phone_number'),
            }, context={
                'request': self.request,
                'view': self
            })
            serializer.is_valid(raise_exception=True)
            return serializer.save()
    