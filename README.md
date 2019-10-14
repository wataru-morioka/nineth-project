## Django Api サーバ
### 概要
アカウント・記事・コメントのリクエスト受付　Restful Api（GET/POST/PUT）
### 機能一覧
- リクエスト受付、レスポンス機能（rest_framework）  
- firebase認証機能利用（匿名認証、google認証）  
- 管理者権限チェック機能  
- CORS対策  
- アカウント情報のDB処理（MySQL）  
- 記事情報のDB処理（MySQL）  
- 記事投稿画像ファイルのアップロード、ダウンロード機能（TODO 権限チェック）  
- コメントのDB処理（MySQL）  
- ORマッパー機能（serializers）  
- SQLによるデータ取得機能（複雑なqueryの場合）  
- DBマイグレーション機能  
- ロギング（/var/log/uwsgi配下）  

