from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
import django_filters
from rest_framework import viewsets, filters, routers
from .models import User, Account
from .serializer import UserSerializer, AccountSerializer
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime

cred = credentials.Certificate(settings.FIREBASE_CERTIFICATE)
firebase_admin.initialize_app(cred)

# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.filter(id=1).first()
#     serializer_class = UserSerializer

# router = routers.DefaultRouter()
# router.register('user', UserViewSet)

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

@csrf_exempt
def account(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        header = request.META.get('HTTP_AUTHORIZATION')
        if header == None:
            res = { 'result': False }
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            print(e)
            res = { 'result': False }
            return JsonResponse(res, status=400)

        try:
            account_list = Account.objects.all()
        except Exception as e:
            print(e)
            res = { 'result': False }
            return JsonResponse(res, status=400)


        
        serializer = AccountSerializer(account_list, many=True)
        # format_list = list(map(
        #     lambda x: datetime.fromisoformat(x['latest_login']).strftime('%Y-%m-%d %H:%M:%S'),
        #      serializer.data
        #      ))

        for item in serializer.data:
            item['latest_login'] = datetime.fromisoformat(item['latest_login']).strftime('%Y-%m-%d %H:%M:%S')
            item['created_datetime'] = datetime.fromisoformat(item['created_datetime']).strftime('%Y-%m-%d %H:%M:%S')
            item['modified_datetime'] = datetime.fromisoformat(item['modified_datetime']).strftime('%Y-%m-%d %H:%M:%S')
            
        res = {
            'result': True,
            'list': serializer.data
        }
        return JsonResponse(res, safe=False)

    elif request.method == 'POST':
        # ヘッダのトークン検証
        header = request.META.get('HTTP_AUTHORIZATION')
        if header == None:
            res = { 'result': False }
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            print(e)
            res = { 'result': False }
            return JsonResponse(res, status=400)

        # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        already_account = Account.objects.filter(uid=uid).first()
        if already_account != None:
            # 更新
            already_account.latest_login = now
            already_account.login_count += 1
            try:
                already_account.save()
                res = { 'result': True }
                return JsonResponse(res, status=201)
            except Exception as e:
                print(e)
                res = { 'result': False }
                return JsonResponse(res, status=500)
            
        request_data = JSONParser().parse(request)
        account = Account(
            uid = uid,
            account = email,
            delete_flag = False,
            webrtc_flag = False,
            admin_flag = False,
            name = request_data.get('name'),
            login_count = 1,
            latest_login = now,
            created_datetime = now,
            modified_datetime = now
        )

        try:
            account.save()
            res = { 'result': True }
            return JsonResponse(res, status=201)
        except Exception as e:
            print(e)
            res = { 'result': False }
            return JsonResponse(res, status=500)


    elif request.method == 'PUT':
        # ヘッダのトークン検証
        header = request.META.get('HTTP_AUTHORIZATION')
        if header == None:
            res = { 'result': False }
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            print(e)
            res = { 'result': False }
            return JsonResponse(res, status=400)

        # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        already_account = Account.objects.filter(uid=uid).first()
        if already_account == None:
            res = { 'result': False }
            return JsonResponse(res, status=500)

        # 更新
        already_account.latest_login = now
        already_account.login_count += 1
        try:
            already_account.save()
            res = { 'result': True }
            return JsonResponse(res, status=201)
        except Exception as e:
            print(e)
            res = { 'result': False }
            return JsonResponse(res, status=500)
        
