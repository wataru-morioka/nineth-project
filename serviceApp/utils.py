from .models import Account, Article, Comment
import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
import traceback

order_dict = {
    '-1': 'created_datetime',
    '0': 'login_count',
    '1': 'latest_login',
    '2': 'modified_datetime',
}

class VerifiedResult:
    def __init__(self, result, decoded_token):
        self.result = result
        self.decoded_token = decoded_token

def verify_token(request, webrtc_flag=None, admin_flag=None):
    # ヘッダのトークン検証
    header = request.META.get('HTTP_AUTHORIZATION')
    if header is None:
        return VerifiedResult(False, None)

    _, id_token = header.split()
    decoded_token = {}
    try:
        decoded_token = auth.verify_id_token(id_token)
    except Exception:
        print(traceback.format_exc())
        return VerifiedResult(False, None)
    
    uid = decoded_token.get('uid')

    if webrtc_flag is not None:
        webrtc_account = Account.objects.filter(uid=uid, webrtc_flag=webrtc_flag).first()
        if webrtc_account is None:
            return VerifiedResult(False, None)

    if admin_flag is not None:
        admin_account = Account.objects.filter(uid=uid, admin_flag=admin_flag).first()
        if admin_account is None:
            return VerifiedResult(False, None)

    return VerifiedResult(True, decoded_token)

def initialize_firebase():
    if (not len(firebase_admin._apps)):
        cred = credentials.Certificate(settings.FIREBASE_CERTIFICATE)
        firebase_admin.initialize_app(cred)

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def get_latest_articles(cursor):
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
                    ' from'
                    ' (' \
                    '   select' \
                    '       id' \
                    '       , contributor_uid' \
                    '       , body' \
                    '       , created_datetime' \
                    '       , modified_datetime' \
                    '   from articles' \
                    '   where' \
                    '       delete_flag = false' \
                    '   order by'
                    '       created_datetime desc'
                    '   limit 3' \
                    ' ) a' \
                    ' left outer join accounts b on' \
                    '   a.contributor_uid = b.uid' \
                    ' left outer join comments c on' \
                    '   a.id = c.article_id' \
                    ' left outer join accounts d on' \
                    '   c.commentator_uid = d.uid' \
                    ' where' \
                    '   c.delete_flag = false or c.delete_flag is null' \
                    ' order by' \
                    '   a.created_datetime desc' \
                    '   , (' \
                    '    case when c.id is not null then' \
                    '       c.created_datetime' \
                    '    end' \
                    '   ) desc'
                )

def get_additional_articles(cursor, current_article_id):
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
                    ' from'
                    ' (' \
                    '   select' \
                    '       id' \
                    '       , contributor_uid' \
                    '       , body' \
                    '       , created_datetime' \
                    '       , modified_datetime' \
                    '   from articles' \
                    '   where' \
                    '       delete_flag = false and id < %s' \
                    '   order by'
                    '       created_datetime desc'
                    '   limit 3' \
                    ' ) a' \
                    ' left outer join accounts b on' \
                    '   a.contributor_uid = b.uid' \
                    ' left outer join comments c on' \
                    '   a.id = c.article_id' \
                    ' left outer join accounts d on' \
                    '   c.commentator_uid = d.uid' \
                    ' where' \
                    '   c.delete_flag = false or c.delete_flag is null' \
                    ' order by' \
                    '   a.created_datetime desc' \
                    '   , (' \
                    '    case when c.id is not null then' \
                    '       c.created_datetime' \
                    '    end' \
                    '   ) desc'
                    , [current_article_id]
                )