"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from serviceApp import views as serviceView
# from siteApp import views as siteView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('api/service/account', serviceView.account),
    path('api/service/registerVipAccount', serviceView.registerVipAccount),
    path('api/service/image', serviceView.image),
    path('api/service/article', serviceView.article),
    path('api/service/comment', serviceView.comment),
    # path('api/site/user', siteView.user),
]

# 動画アップロード先指定
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)