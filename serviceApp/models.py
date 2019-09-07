from django.db import models

class User(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        db_table = 'users'

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

