import os

class Config:
    SECRET_KEY = 'chave-super-secreta'  # você pode trocar por um valor mais seguro depois
    DEBUG = True
    DATABASE_FILE = 'backend/database.json'
    UPLOAD_FOLDER = 'backend/static/uploads'