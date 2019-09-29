from rest_framework import serializers
from .models import User, Account, Article, Comment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class ArticleSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    # accounts = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id',
            'orner', 
            'contributor_uid', 
            'contributor_account', 
            'body', 
            'delete_flag', 
            'created_datetime', 
            'modified_datetime', 
            'comments',
            # 'accounts'
        ]

    def get_comments(self, obj):
        qs = Comment.objects.all().filter(article_id = Article.objects.get(id=obj.id)).order_by('modified_datetime').reverse()
        return CommentSerializer(qs, many=True, read_only=True).data

    # def get_accounts(self, obj):
    #     print('testtest')
    #     qs = Account.objects.filter(uid = Article.objects.get(contributor_uid=obj.contributor_uid)).first()
    #     print(qs)
    #     return AccountSerializer(qs, many=True, read_only=True).data

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'