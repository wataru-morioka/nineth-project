from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser, FileUploadParser
import django_filters
from rest_framework import viewsets, filters, routers
from rest_framework.decorators import parser_classes, api_view
from .models import Account, Article, Comment
from .serializer import AccountSerializer, ArticleSerializer, CommentSerializer
# import firebase_admin
# from firebase_admin import credentials, auth
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
from .utils import initialize_firebase, verify_token, dictfetchall, order_dict, \
                    get_latest_articles, get_additional_articles

initialize_firebase()

# ブログ記事の画像アップロード時（レスポンスはCKEditor.js api 仕様）
@csrf_exempt
def image(request):
    res = {
        "uploaded": False,
        "error": {
            "message": "Error"
        }
    }
    if request.method == 'POST' and request.FILES['upload']:
        upload_file = request.FILES['upload']
        fs = FileSystemStorage()
        filename = ''

        try:
            # ブログ記事画像用mediaディレクトリに保存
            filename = fs.save(upload_file.name, upload_file)
        except Exception:
            print(traceback.format_exc())
            return JsonResponse(res, status=500)

        uploaded_file_url = fs.url(filename)
        res = {
            "url": 'https://django.service{}'.format(uploaded_file_url),
            "uploaded": True
        }
        return JsonResponse(res, status=201)

    return JsonResponse(res, status=400)

# ブログ記事に対するコメントpost時
@csrf_exempt
@api_view(['POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def comment(request, format=None):
    res = { 'result': False }
    if request.method == 'POST':
        # アカウント登録者のみOK
        verified_result = verify_token(request, webrtc_flag=True)
        if not verified_result.result:
            return JsonResponse(res, status=400)

        decoded_token = verified_result.decoded_token
        print(decoded_token)

        article_id = request.data.get('articleId')
        article = Article.objects.filter(id=article_id).first()
        if article is None:
            return JsonResponse(res, status=400)

        now = datetime.now()
        comment = Comment(
            article = article,
            commentator_uid = decoded_token.get('uid'),
            commentator_account = decoded_token.get('email'),
            body = request.data.get('body'),
            created_datetime = now,
            modified_datetime = now
        )

        if Comment.insert(comment):
            res = { 'result': True }
            return JsonResponse(res, status=201)
        else:
            return JsonResponse(res, status=500)

# ブログ記事の取得、投稿、変更 api
@csrf_exempt
@api_view(['GET', 'POST', 'PUT'])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def article(request, format=None):
    res = { 'result': False }

    # 記事取得
    if request.method == 'GET':
        # firebase匿名認証（サイト閲覧者）権限以上さえあればOK
        verified_result = verify_token(request)
        if not verified_result.result:
            return JsonResponse(res, status=400)

        articleList = []
        current_article_id = request.GET.get(key='current_article_id', default='')
        additional_flag = request.GET.get(key='additional_flag', default='')

        try:
            with connection.cursor() as cursor:
                if current_article_id == str(0) or not strtobool(additional_flag):
                    # 初期記事取得時、もしくは記事、コメント更新時は、最新記事3件取得
                    get_latest_articles(cursor)
                else:
                    # 画面スクロールし追加記事取得時（現在表示されている記事より古い記事3件）
                    get_additional_articles(cursor, current_article_id)

                articleList = dictfetchall(cursor)

            for article in articleList:
                article['created_datetime'] = article['created_datetime'].strftime('%Y-%m-%d %H:%M:%S')
                article['modified_datetime'] = article['modified_datetime'].strftime('%Y-%m-%d %H:%M:%S')
                article['thumbnail'] = base64.b64encode(article['thumbnail']).decode('utf-8')
                if article['commentator_thumbnail'] is not None:
                    # バイナリデータはbase64エンコード
                    article['commentator_thumbnail'] = base64.b64encode(article['commentator_thumbnail']).decode('utf-8')

            res = {
                'result': True,
                'articleList': articleList,
            }
            return JsonResponse(res, safe=False)
        except Exception:
            print(traceback.format_exc())
            return JsonResponse(res, status=500)

    # 記事投稿
    if request.method == 'POST':
        # 管理者であればOK
        verified_result = verify_token(request, admin_flag=True)
        if not verified_result.result:
            return JsonResponse(res, status=400)

        decoded_token = verified_result.decoded_token
        print(decoded_token)

        now = datetime.now()
        article = Article(
            orner = 'jagermeister',
            contributor_uid = decoded_token.get('uid'),
            contributor_account = decoded_token.get('email'),
            body = request.data.get('body'),
            created_datetime = now,
            modified_datetime = now
        )

        # 新規記事挿入
        if Article.upsert(article):
            res = { 'result': True }
            return JsonResponse(res, status=201)
        else :
            return JsonResponse(res, status=500)
    
    # 記事変更
    if request.method == 'PUT':
        # 管理者であればOK
        verified_result = verify_token(request, admin_flag=True)
        if not verified_result.result:
            JsonResponse(res, status=400)

        decoded_token = verified_result.decoded_token
        print(decoded_token)

        article_id = request.data.get('articleId')
        already_article = Article.objects.filter(id=article_id).first()

        # 記事データが存在するか確認
        if already_article is None:
            return JsonResponse(res, status=400)

        now = datetime.now()
        already_article.body = request.data.get('body')
        already_article.modified_datetime = now

        # 記事変更
        if Article.upsert(already_article):
            res = { 'result': True }
            return JsonResponse(res, status=201)
        else :
            return JsonResponse(res, status=500)

@csrf_exempt
@api_view(['PUT'])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def registerVipAccount(request, format=None):
    res = { 'result': False }
    if request.method == 'PUT':
        # サイト閲覧者であるかどうか確認
        verified_result = verify_token(request)
        if not verified_result.result:
            return JsonResponse(res, status=400)

        decoded_token = verified_result.decoded_token
        print(decoded_token)
        
        # firebase google認証（ログイン）さえしていればOK
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

        # account情報更新
        if Account.upsert(already_account):
            res = { 
                'result': True,
                'thumbnail': base64.b64encode(already_account.thumbnail).decode('utf-8'),
                'state': already_account.state
            }
            return JsonResponse(res, status=201)
        else :
            return JsonResponse(res, status=500)

@csrf_exempt
def account(request):
    res = { 'result': False }

    # 管理画面に対してアカウント情報を取得
    if request.method == 'GET':
        # 管理者であればOK
        verified_result = verify_token(request, admin_flag=True)
        if not verified_result.result:
            return JsonResponse(res, status=400)

        decoded_token = verified_result.decoded_token
        print(decoded_token)

        total_count = 0
        account_list = []
        search_string = request.GET.get(key='search', default='')
        order = order_dict.get(request.GET.get(key='order', default=-1))
        order_type = request.GET.get(key='type', default=True)
        try:
            # 検索文字がない場合
            if len(search_string) == 0:
                total_count = Account.objects.all().count()
                # リストの並び順を考慮
                if strtobool(order_type):
                    account_list = Account.objects.all().order_by(order).reverse()[:100]
                else:
                    account_list = Account.objects.all().order_by(order)[:100]
            # 検索文字がある場合
            else:
                total_count = Account.objects.filter(
                        Q(account__icontains=search_string) |
                        Q(name__icontains=search_string)
                    ).all().count()

                # リストの並び順を考慮
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
        except Exception:
            print(traceback.format_exc())
            return JsonResponse(res, status=400)

        serializer = AccountSerializer(account_list, many=True)

        for item in serializer.data:
            item['latest_login'] = datetime.fromisoformat(item['latest_login']).strftime('%Y-%m-%d %H:%M:%S')
            item['created_datetime'] = datetime.fromisoformat(item['created_datetime']).strftime('%Y-%m-%d %H:%M:%S')
            item['modified_datetime'] = datetime.fromisoformat(item['modified_datetime']).strftime('%Y-%m-%d %H:%M:%S')
            
        res = {
            'result': True,
            'totalCount': total_count,
            'accountList': serializer.data
        }
        return JsonResponse(res, safe=False)

    # ユーザがhome画面のLoginボタンからgoogle認証をしてきた場合
    elif request.method == 'POST':
        # サイト閲覧者であるかどうか確認
        verified_result = verify_token(request)
        if not verified_result.result:
            return JsonResponse(res, status=400)

        decoded_token = verified_result.decoded_token
        print(decoded_token)

        # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')

        if email is None:
            return JsonResponse(res, status=400)

        already_account = Account.objects.filter(uid=uid).first()

        # すでに一度はgoogle認証（ログイン）していた場合
        if already_account is not None:
            # 更新
            already_account.email = email
            already_account.name = decoded_token.get('name')
            already_account.latest_login = now
            # already_account.login_count += 1

            if Account.upsert(already_account):
                res = { 'result': True }
                return JsonResponse(res, status=201)
            else:
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

        # ユーザgoggleアカウント情報を新規登録
        if Account.upsert(account):
            res = { 'result': True }
            return JsonResponse(res, status=201)
        else:
            return JsonResponse(res, status=500)

    # アカウント情報更新時
    elif request.method == 'PUT':
        # サイト閲覧者であるかどうか確認
        verified_result = verify_token(request)
        if not verified_result.result:
            return JsonResponse(res, status=400)

        decoded_token = verified_result.decoded_token
        print(decoded_token)

        # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        uid = decoded_token.get('uid')
        request_data = JSONParser().parse(request)
        webrtc_flag = request_data.get('webrtc')
        admin_flag = request_data.get('admin')
        delete_flag = request_data.get('delete')
        
        # 一般サイトに訪問してきた時
        if webrtc_flag is None:
            # googlen認証（ログイン）済みだった場合、ログインカウントを更新
            already_account = Account.objects.filter(uid=uid).first()
            if already_account is None:
                return JsonResponse(res, status=500)

            already_account.latest_login = now
            already_account.login_count += 1

            # アカウント情報更新
            if Account.upsert(already_account):
                thumbnail = {}

                # サムネイルが登録されている（ユーザがサイトアカウント登録をした）場合、レスポンスにサムネイルを加える
                if already_account.thumbnail is None:
                    thumbnail = None
                else:
                    thumbnail = base64.b64encode(already_account.thumbnail).decode('utf-8')
                res = { 
                    'result': True,
                    'thumbnail': thumbnail,
                    'state': already_account.state,
                    'isVip': already_account.webrtc_flag,
                    'isAdmin': already_account.admin_flag,
                }
                return JsonResponse(res, status=201)
            else:
                return JsonResponse(res, status=500)

        # 管理画面からユーザアカウント情報を更新した時       
        else:
            # 管理者であればOK
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

            # アカウント情報更新
            if Account.upsert(already_account):
                res = { 'result': True }
                return JsonResponse(res, status=201)
            else:
                return JsonResponse(res, status=500)
