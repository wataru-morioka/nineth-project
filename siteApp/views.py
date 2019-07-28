from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
import django_filters
from rest_framework import viewsets, filters, routers
from .models import User
from .serializer import UserSerializer

@csrf_exempt
def user(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        user = User.objects.filter(id=1).first()
        # serializer = UserSerializer(User, many=True)
        serializer = UserSerializer(user)
        return JsonResponse(serializer.data, safe=False)

    # elif request.method == 'POST':
    #     data = JSONParser().parse(request)
    #     serializer = SnippetSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return JsonResponse(serializer.data, status=201)
    #     return JsonResponse(serializer.errors, status=400)