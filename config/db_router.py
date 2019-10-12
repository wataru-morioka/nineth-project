class DbRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'siteApp':
            return 'siteApp'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'siteApp':
            return 'siteApp'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'siteApp' or \
           obj2._meta.app_label == 'siteApp':
           return True

    def allow_migrate(self, db, app_label, model=None, **hints):
        if app_label == 'siteApp':
            return db == 'siteApp'