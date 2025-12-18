from flask import Flask, redirect, url_for
from config import Config
from database import db
from routes.energy_routes import energy_bp
from models import FactoryArea, EnergyMeter, EnergyMonitor, PeakValleyEnergy
import datetime

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.config.from_object(Config)

# 绑定数据库
db.init_app(app)

# 注册蓝图
app.register_blueprint(energy_bp, url_prefix='/energy')

@app.route('/')
def index():
    return redirect(url_for('energy.meter_manage'))

# --- 造数据函数 (仅在数据库为空时执行) ---
def init_db_data():
    # 创建所有表
    db.create_all()
    
    # 检查是否已有数据
    if FactoryArea.query.first():
        return

    print("正在初始化测试数据...")
    
    # 1. 创建厂区
    f1 = FactoryArea(factory_id="F001", factory_name="真旺厂", address="北京市海淀区", manager="张三")
    f2 = FactoryArea(factory_id="F002", factory_name="豆果厂", address="北京市朝阳区", manager="李四")
    db.session.add_all([f1, f2])
    db.session.commit()
    
    # 2. 创建设备
    m1 = EnergyMeter(
        meter_id="M_WATER_01", factory_id="F001", energy_type="水", 
        install_location="污水处理站", pipe_spec="DN100", comm_protocol="RS485", 
        calib_cycle=12, manufacturer="西门子"
    )
    m2 = EnergyMeter(
        meter_id="M_ELEC_01", factory_id="F001", energy_type="天然气", 
        install_location="锅炉房", pipe_spec="DN50", comm_protocol="Lora", 
        run_status="故障", calib_cycle=24, manufacturer="施耐德"
    )
    db.session.add_all([m1, m2])
    db.session.commit()
    
    # 3. 创建监测数据
    d1 = EnergyMonitor(
        data_id="D001", meter_id="M_WATER_01", collect_time=datetime.datetime.now(),
        energy_value=120.5, unit="m³", data_quality="优", factory_id="F001", is_verified=True
    )
    d2 = EnergyMonitor(
        data_id="D002", meter_id="M_ELEC_01", collect_time=datetime.datetime.now(),
        energy_value=50.2, unit="m³", data_quality="差", factory_id="F001", is_verified=False
    )
    db.session.add_all([d1, d2])
    
    # 4. 创建峰谷数据 (用于报表)
    pv1 = PeakValleyEnergy(
        record_id="PV001", energy_type="电", factory_id="F001", stat_date=datetime.date.today(),
        peak_energy=100, high_energy=200, flat_energy=150, valley_energy=50,
        total_energy=500, peak_valley_price=0.8, energy_cost=400
    )
    db.session.add(pv1)
    db.session.commit()
    
    print("测试数据初始化完成！")

if __name__ == '__main__':
    with app.app_context():
        init_db_data() # 启动前先检查并造数据
    app.run(debug=True, port=5000)