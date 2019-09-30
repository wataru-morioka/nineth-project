from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser, FileUploadParser
import django_filters
from rest_framework import viewsets, filters, routers
from rest_framework.decorators import parser_classes, api_view
from .models import User, Account, Article, Comment
from .serializer import UserSerializer, AccountSerializer, ArticleSerializer, CommentSerializer
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime
from django.db.models import Q
from distutils.util import strtobool
import base64
from django.core.files.storage import FileSystemStorage
import traceback
from django.db.models.sql.datastructures import Join
from django.db.models.fields.related import ForeignObject
from django.db.models.options import Options
from django.db import connection

cred = credentials.Certificate(settings.FIREBASE_CERTIFICATE)
firebase_admin.initialize_app(cred)

order_dict = {
    '-1': 'created_datetime',
    '0': 'login_count',
    '1': 'latest_login',
    '2': 'modified_datetime',
}

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

@csrf_exempt
def user(request):
    if request.method == 'GET':
        user = User.objects.filter(id=1).first()
        # serializer = UserSerializer(User, many=True)
        serializer = UserSerializer(user)
        return JsonResponse(serializer.data, safe=False)

@csrf_exempt
def image(request):
    if request.method == 'POST' and request.FILES['upload']:
        upload_file = request.FILES['upload']
        fs = FileSystemStorage()
        filename = fs.save(upload_file.name, upload_file)
        uploaded_file_url = fs.url(filename)
        res = {
            "url": 'https://django.service{}'.format(uploaded_file_url),
            "uploaded": True
        }
        return JsonResponse(res, status=201)

    res = {
        "uploaded": False,
        "error": {
            "message": "Error"
        }
    }
    return JsonResponse(res, status=400)

@csrf_exempt
@api_view(['POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def comment(request, format=None):
    if request.method == 'POST':
        # ヘッダのトークン検証
        res = { 'result': False }
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
            print(decoded_token)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=400)
        
        uid = decoded_token.get('uid')
        webrtc_account = Account.objects.filter(uid=uid, webrtc_flag=True).first()
        if webrtc_account is None:
            return JsonResponse(res, status=400)

        article_id = request.data.get('articleId')
        article = Article.objects.filter(id=article_id).first()
        if article is None:
            return JsonResponse(res, status=400)

        now = datetime.now()
        comment = Comment(
            article = article,
            commentator_uid = uid,
            commentator_account = decoded_token.get('email'),
            body = request.data.get('body'),
            created_datetime = now,
            modified_datetime = now
        )

        try:
            comment.save()
            res = { 'result': True }
            return JsonResponse(res, status=201)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=500)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT'])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def article(request, format=None):
    if request.method == 'GET':
        # ヘッダのトークン検証
        res = { 'result': False }
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
            print(decoded_token)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=400)

        articleList = []
        with connection.cursor() as cursor:
            cursor.execute(
                'select' \
                '   a.id as id' \
                '   ,b.name as contributor_name' \
                '   ,a.body as body' \
                '   ,b.thumbnail as thumbnail' \
                '   ,a.created_datetime as created_datetime' \
                '   ,a.modified_datetime as modified_datetime' \
                '   ,d.name as commentator_name' \
                '   ,d.thumbnail as commentator_thumbnail' \
                '   ,c.body as comment_body' \
                '   ,c.created_datetime as comment_created_datetime' \
                ' from articles a left outer join accounts b on' \
                '   a.contributor_uid = b.uid and a.delete_flag = false' \
                ' left outer join comments c on' \
                '   a.id = c.article_id and c.delete_flag = false' \
                ' left outer join accounts d on' \
                '   c.commentator_uid = d.uid' \
                ' order by a.created_datetime desc, c.created_datetime desc'
            )
            articleList = dictfetchall(cursor)

        try:
            # serializer = ArticleSerializer(article_list, many=True)
            for article in articleList:
                article['created_datetime'] = article['created_datetime'].strftime('%Y-%m-%d %H:%M:%S')
                article['modified_datetime'] = article['modified_datetime'].strftime('%Y-%m-%d %H:%M:%S')
                article['thumbnail'] = base64.b64encode(article['thumbnail']).decode('utf-8')
                if article['commentator_thumbnail'] is not None:
                    article['commentator_thumbnail'] = base64.b64encode(article['commentator_thumbnail']).decode('utf-8')
                print(article['contributor_name'])

            res = {
                'result': True,
                'articleList': articleList,
            }
            
            return JsonResponse(res, safe=False)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return JsonResponse(res, status=500)

    if request.method == 'POST':
        # ヘッダのトークン検証
        res = { 'result': False }
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
            print(decoded_token)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=400)
        
        uid = decoded_token.get('uid')
        admin_account = Account.objects.filter(uid=uid, admin_flag=True).first()
        if admin_account is None:
            return JsonResponse(res, status=400)

        now = datetime.now()
        article = Article(
            orner = 'jagermeister',
            contributor_uid = uid,
            contributor_account = decoded_token.get('email'),
            body = request.data.get('body'),
            created_datetime = now,
            modified_datetime = now
        )
        try:
            article.save()
            res = { 'result': True }
            return JsonResponse(res, status=201)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=500)
    
    if request.method == 'PUT':
        # ヘッダのトークン検証
        res = { 'result': False }
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
            print(decoded_token)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=400)
        
        uid = decoded_token.get('uid')
        admin_account = Account.objects.filter(uid=uid, admin_flag=True).first()
        if admin_account is None:
            return JsonResponse(res, status=400)

        article_id = request.data.get('articleId')
        already_article = Article.objects.filter(id=article_id).first()
        if already_article is None:
            return JsonResponse(res, status=400)

        now = datetime.now()
        already_article.body = request.data.get('body')
        already_article.modified_datetime = now
        try:
            already_article.save()
            res = { 'result': True }
            return JsonResponse(res, status=201)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=500)

@csrf_exempt
@api_view(['PUT'])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def registerVipAccount(request, format=None):
    if request.method == 'PUT':
        # ヘッダのトークン検証
        res = { 'result': False }
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
            print(decoded_token)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=400)
        
        uid = decoded_token.get('uid')
        already_account = Account.objects.filter(uid=uid).first()
        if already_account is None:
            return JsonResponse(res, status=400)

        now = datetime.now()
        state = request.data.get('state')
        upload_file = request.data.get('file')
        if upload_file is not None:
            thumbnail = request.data.get('file').read()
            already_account.thumbnail = thumbnail
        already_account.state = state
        already_account.modified_datetime = now
        try:
            already_account.save()
            res = { 'result': True, 'thumbnail': base64.b64encode(already_account.thumbnail).decode('utf-8') }
            # res = { 'result': True }
            return JsonResponse(res, status=201)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=500)

@csrf_exempt
def account(request):
    if request.method == 'GET':
        res = { 'result': False }
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return JsonResponse(res, status=400)
        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=400)

        uid = decoded_token.get('uid')
        admin_account = Account.objects.filter(uid=uid, admin_flag=True).first()
        if admin_account is None:
            return JsonResponse(res, status=400)

        total_count = 0
        account_list = []
        search_string = request.GET.get(key='search', default='')
        order = order_dict.get(request.GET.get(key='order', default=-1))
        order_type = request.GET.get(key='type', default=True)
        try:
            if len(search_string) == 0:
                total_count = Account.objects.all().count()
                if strtobool(order_type):
                    account_list = Account.objects.all().order_by(order).reverse()[:100]
                else:
                    account_list = Account.objects.all().order_by(order)[:100]
            else:
                total_count = Account.objects.filter(
                        Q(account__icontains=search_string) |
                        Q(name__icontains=search_string)
                    ).all().count()
                if strtobool(order_type):
                    account_list = Account.objects.filter(
                        Q(account__icontains=search_string) |
                        Q(name__icontains=search_string)
                    ).order_by(order).reverse().all()[:100]
                else:
                    account_list = Account.objects.filter(
                        Q(account__icontains=search_string) |
                        Q(name__icontains=search_string)
                    ).order_by(order).all()[:100]
        except Exception as e:
            print(e)
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
            # item['thumbnail'] = None
            
        res = {
            'result': True,
            'totalCount': total_count,
            'accountList': serializer.data
        }
        return JsonResponse(res, safe=False)

    elif request.method == 'POST':
        res = { 'result': False }
        # ヘッダのトークン検証
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=400)

        # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')

        if email is None:
            return JsonResponse(res, status=400)

        already_account = Account.objects.filter(uid=uid).first()
        if already_account is not None:
            # 更新
            already_account.email = email
            already_account.name = decoded_token.get('name')
            already_account.latest_login = now
            already_account.login_count += 1
            try:
                already_account.save()
                res = { 'result': True }
                return JsonResponse(res, status=201)
            except Exception as e:
                print(e)
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
            return JsonResponse(res, status=500)


    elif request.method == 'PUT':
        # ヘッダのトークン検証
        res = { 'result': False }
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return JsonResponse(res, status=400)

        _, id_token = header.split()
        decoded_token = {}
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            print(e)
            return JsonResponse(res, status=400)

        # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        uid = decoded_token.get('uid')
        request_data = JSONParser().parse(request)
        webrtc_flag = request_data.get('webrtc')
        admin_flag = request_data.get('admin')
        delete_flag = request_data.get('delete')
        
        if webrtc_flag is None:
            already_account = Account.objects.filter(uid=uid).first()
            if already_account is None:
                return JsonResponse(res, status=500)

            already_account.latest_login = now
            already_account.login_count += 1
            try:
                already_account.save()

                thumbnail = {}
                if already_account.thumbnail is None:
                    thumbnail = None
                else:
                    thumbnail = base64.b64encode(already_account.thumbnail).decode('utf-8')
                res = { 'result': True, 'thumbnail': thumbnail, 'state': already_account.state }
                
                return JsonResponse(res, status=201)
            except Exception as e:
                print(e)
                return JsonResponse(res, status=500)
        else:
            admin_account = Account.objects.filter(uid=uid, admin_flag=True).first()
            if admin_account is None:
                return JsonResponse(res, status=400)

            uid = request_data.get('uid')
            print(uid)
            already_account = Account.objects.filter(uid=uid).first()
            already_account.webrtc_flag = webrtc_flag
            already_account.admin_flag = admin_flag
            already_account.delete_flag = delete_flag
            already_account.modified_datetime = now

            try:
                already_account.save()
                res = { 'result': True }
                return JsonResponse(res, status=201)
            except Exception as e:
                print(e)
                return JsonResponse(res, status=500)
