from pymongo import MongoClient

class DatabaseProxy:
    def __init__(self):
        self._db = None
    def bind(self, database):
        self._db = database
    def __getattr__(self, name):
        if self._db is None:
            raise RuntimeError('MongoDB todavía no ha sido inicializado.')
        return getattr(self._db, name)

mongo_client = None
db = DatabaseProxy()

def init_mongo(app):
    global mongo_client
    mongo_client = MongoClient(app.config['MONGO_URI'])
    database = mongo_client[app.config['MONGO_DB']]
    db.bind(database)
    database.users.create_index('email', unique=True)
    database.roles.create_index('name', unique=True)
    database.categories.create_index('name', unique=True)
    database.activity_logs.create_index([('created_at', -1)])
    database.documents.create_index([('created_at', -1)])
    return database
