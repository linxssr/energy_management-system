from flask_sqlalchemy import SQLAlchemy

# 初始化 SQLAlchemy，但不绑定 app，稍后在 app.py 中绑定
db = SQLAlchemy()