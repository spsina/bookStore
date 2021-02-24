from django.shortcuts import render
from rest_framework import generics
from .serializers import UserProfileSerializer
from .models import UserProfile
from .permissions import IsLoggedIn

class UserProfileCreateView(generics.CreateAPIView):
    serializer_class = UserProfileSerializer


class UserProfileRUDView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()
    permission_classes = (IsLoggedIn, )

    lookup_field = 'pk'
    lookup_url_kwarg = 'user_profile_id'
