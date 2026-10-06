"""Importa a MongoDB los datos convertidos del innovafile.sql original.

Uso desde la raíz del proyecto:
    python scripts/import_data.py

Por defecto NO borra la base. Usa --reset si quieres reemplazar las colecciones
principales antes de importar:
    python scripts/import_data.py --reset
"""
import os, sys, json, argparse
from pathlib import Path
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')

URI = os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27017/')
DB_NAME = os.getenv('MONGO_DB', 'innovafile')
DATA = ROOT / 'data'


def load(name):
    with open(DATA / f'{name}.json', encoding='utf-8') as f:
        return json.load(f)


def dt(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    except Exception:
        return value


def main(reset=False):
    client = MongoClient(URI)
    db = client[DB_NAME]
    client.admin.command('ping')
    if reset:
        for c in ['activity_logs','documents','users','categories','roles']:
            db[c].delete_many({})

    role_map = {}
    for r in load('roles'):
        old = r.pop('id')
        r['legacy_id'] = old
        r['created_at'] = dt(r.get('created_at')); r['updated_at'] = dt(r.get('updated_at'))
        res = db.roles.update_one({'legacy_id':old}, {'$set':r}, upsert=True)
        doc = db.roles.find_one({'legacy_id':old}); role_map[old] = doc['_id']

    category_map = {}
    for c in load('categories'):
        old=c.pop('id'); c['legacy_id']=old
        c['created_at']=dt(c.get('created_at')); c['updated_at']=dt(c.get('updated_at'))
        db.categories.update_one({'legacy_id':old},{'$set':c},upsert=True)
        category_map[old]=db.categories.find_one({'legacy_id':old})['_id']

    user_map={}
    for u in load('users'):
        old=u.pop('id'); old_role=u.pop('role_id'); u['legacy_id']=old
        u['role_id']=role_map.get(old_role)
        u['created_at']=dt(u.get('created_at')); u['updated_at']=dt(u.get('updated_at'))
        u.pop('email_verified_at',None); u.pop('remember_token',None)
        db.users.update_one({'legacy_id':old},{'$set':u},upsert=True)
        user_map[old]=db.users.find_one({'legacy_id':old})['_id']

    for d in load('documents'):
        old=d.pop('id'); old_cat=d.pop('category_id'); old_user=d.pop('user_id'); d['legacy_id']=old
        d['category_id']=category_map.get(old_cat); d['user_id']=user_map.get(old_user)
        d['file_path']='static/uploads/'+d.get('file_path','')
        d['created_at']=dt(d.get('created_at')); d['updated_at']=dt(d.get('updated_at'))
        db.documents.update_one({'legacy_id':old},{'$set':d},upsert=True)

    for a in load('activity_logs'):
        old=a.pop('id'); old_user=a.pop('user_id'); a['legacy_id']=old; a['user_id']=user_map.get(old_user)
        a['created_at']=dt(a.get('created_at')); a['updated_at']=dt(a.get('updated_at'))
        db.activity_logs.update_one({'legacy_id':old},{'$set':a},upsert=True)

    db.users.create_index('email', unique=True)
    db.roles.create_index('name', unique=True)
    db.categories.create_index('name', unique=True)
    print(f'Importación terminada en MongoDB: {DB_NAME}')
    print('Roles:', db.roles.count_documents({}))
    print('Usuarios:', db.users.count_documents({}))
    print('Categorías:', db.categories.count_documents({}))
    print('Documentos:', db.documents.count_documents({}))
    print('Actividades:', db.activity_logs.count_documents({}))

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--reset', action='store_true')
    args=parser.parse_args()
    main(args.reset)
