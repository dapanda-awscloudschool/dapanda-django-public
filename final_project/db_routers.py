class MasterSlaveRouter:
    """
    A router to control all database operations on models for different
    databases.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to read models go to replica.
        """
        return 'replica'

    def db_for_write(self, model, **hints):
        """
        Attempts to write models go to default.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the default or replica databases is
        involved.
        """
        db_list = ('default', 'replica')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth app only appears in the 'default' database.
        """
        return db == 'default'
