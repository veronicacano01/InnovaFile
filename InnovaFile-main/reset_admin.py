import bcrypt
from datetime import datetime, timezone
from app import create_app
from extensions import db

app=create_app()
with app.app_context():
    role=db.roles.find_one({'name':'Administrador'})
    if not role:
        db.roles.insert_one({'name':'Administrador','description':'Acceso completo al sistema','created_at':datetime.now(timezone.utc),'updated_at':datetime.now(timezone.utc)})
        role=db.roles.find_one({'name':'Administrador'})
    email='admin@innovafile.com'; password='Admin123!'
    db.users.update_one({'email':email},{'$set':{'name':'Administrador','last_name':'InnovaFile','email':email,'password':bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode(),'role_id':role['_id'],'updated_at':datetime.now(timezone.utc)},'$setOnInsert':{'created_at':datetime.now(timezone.utc)}},upsert=True)
    print(f'Acceso listo: {email} / {password}')
