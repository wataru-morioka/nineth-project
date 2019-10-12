from django.db import models
import traceback
from distutils.util import strtobool
from django.db.models import Q

class Account(models.Model):
    uid = models.CharField(db_index=True, max_length=64, unique=True, null=False, default='')
    account = models.EmailField(max_length=255, null=False, default='')
    delete_flag = models.BooleanField(null=False, default=False)
    webrtc_flag = models.BooleanField(null=False, default=False)
    admin_flag = models.BooleanField(null=False, default=False)
    name = models.CharField(max_length=64, null=False)
    state = models.CharField(max_length=16, null=True)
    login_count = models.IntegerField(db_index=True, null=False, default=1)
    latest_login = models.DateTimeField(db_index=True, null=False)
    created_datetime = models.DateTimeField(db_index=True, null=False)
    modified_datetime = models.DateTimeField(db_index=True, null=False)
    thumbnail = models.BinaryField(null=True)

    class Meta:
        db_table = 'accounts'

    # def __init__(self, delete_flag, webrtc_flag, admin_flag, account, name, state, login_count, created_datetime, modified_datetime):
    #     self.delete_flag = delete_flag
    #     self.webrtc_flag = webrtc_flag
    #     self.admin_flag = admin_flag
    #     self.account = account
    #     self.name = name
    #     self.state = state
    #     self.login_count = login_count
    #     self.created_datetime = created_datetime
    #     self.modified_datetime = modified_datetime

    def upsert(self):
        try:
            self.save()
            return True
        except Exception:
            print(traceback.format_exc())
            return False

    @staticmethod
    def query(account_list, search_string, order, order_type):
        total_count = 0
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
            return (total_count, account_list)
        except Exception:
            print(traceback.format_exc())
            return (False, None)


class Article(models.Model):
    orner = models.CharField(max_length=255, null=False, default='')
    contributor_uid = models.CharField(max_length=255, db_index=True, null=False, default='')
    contributor_account = models.CharField(max_length=255, db_index=True, null=False, default='')
    body = models.TextField(db_index=True, null=False)
    video_path = models.FilePathField(null=True)
    video_thumbnail = models.BinaryField(db_index=True, null=True)
    delete_flag = models.BooleanField(db_index=True, null=False, default=False)
    created_datetime = models.DateTimeField(db_index=True, null=False)
    modified_datetime = models.DateTimeField(db_index=True, null=False)

    class Meta:
        db_table = 'articles'

    def upsert(self):
        try:
            self.save()
            return True
        except Exception:
            print(traceback.format_exc())
            return False

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    commentator_uid = models.CharField(max_length=255, db_index=True, null=False, default='')
    commentator_account = models.CharField(max_length=255, db_index=True, null=False, default='')
    body = models.TextField(db_index=True, null=False)
    delete_flag = models.BooleanField(db_index=True, null=False, default=False)
    created_datetime = models.DateTimeField(db_index=True, null=False)
    modified_datetime = models.DateTimeField(db_index=True, null=False)

    class Meta:
        db_table = 'comments'

    def insert(self):
        try:
            self.save()
            return True
        except Exception:
            print(traceback.format_exc())
            return False

