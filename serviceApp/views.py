from django.shortcuts import render

# Create your views here.
import django_filters
from rest_framework import viewsets, filters
from .models import User
from .serializer import UserSerializer
