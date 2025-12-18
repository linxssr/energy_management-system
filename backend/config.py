import os
from dotenv import load_dotenv

# 加载环境变量（如果你有 .env 文件的话）
load_dotenv()

class Config:
    # --- Flask基础配置 ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_energy_key_2025")
    DEBUG = True  # 开发阶段设为 True
    
    # --- MySQL数据库配置 ---
    # 确保这里的 root:123456 和 energy_db 与你在 MySQL Workbench 中创建的一致
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:12345678@localhost:3306/energy_db?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- 峰谷时段配置 (报表功能必须用到) ---
    PEAK_VALLEY_PERIODS = {
        "peak": ["10:00-12:00", "16:00-18:00"],        # 尖峰时段
        "high": ["08:00-10:00", "12:00-16:00", "18:00-22:00"],  # 高峰时段
        "flat": ["06:00-08:00", "22:00-24:00"],        # 平段时段
        "valley": ["00:00-06:00"]                      # 低谷时段
    }
    
    # --- 峰谷电价 (元/kWh) ---
    PEAK_VALLEY_PRICES = {
        "peak": 1.2,    # 尖峰电价
        "high": 0.9,    # 高峰电价
        "flat": 0.6,    # 平段电价
        "valley": 0.3   # 低谷电价
    }