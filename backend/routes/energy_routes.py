from flask import Blueprint, render_template, request, jsonify
from database import db
from models import EnergyMeter, EnergyMonitor, PeakValleyEnergy, FactoryArea
from sqlalchemy import func
from datetime import datetime

energy_bp = Blueprint('energy', __name__)

# --- 辅助函数：统一返回 ---
def success_resp(msg="操作成功", data=None):
    return jsonify({"success": True, "message": msg, "data": data})

def error_resp(msg="操作失败"):
    return jsonify({"success": False, "message": msg})

# --- 1. 能耗计量设备管理 ---
@energy_bp.route('/meter_manage')
def meter_manage():
    # 获取筛选参数
    e_type = request.args.get('energy_type')
    r_status = request.args.get('run_status')
    
    # 构建查询
    query = EnergyMeter.query
    if e_type:
        query = query.filter_by(energy_type=e_type)
    if r_status:
        query = query.filter_by(run_status=r_status)
    
    meters = query.all()
    return render_template('meter_manage.html', meters=meters)

# --- 2. 能耗监测数据 ---
@energy_bp.route('/monitor_data')
def monitor_data():
    # 获取筛选参数
    meter_id = request.args.get('meter_id')
    factory_id = request.args.get('factory_id')
    quality = request.args.get('data_quality')
    start_time = request.args.get('start_time')
    
    # 查询所有厂区用于下拉框
    factories = [f.factory_id for f in FactoryArea.query.all()]
    
    query = EnergyMonitor.query
    if meter_id:
        query = query.filter(EnergyMonitor.meter_id.like(f"%{meter_id}%"))
    if factory_id:
        query = query.filter_by(factory_id=factory_id)
    if quality:
        query = query.filter_by(data_quality=quality)
    if start_time:
        # 转换时间字符串
        try:
            dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
            query = query.filter(EnergyMonitor.collect_time >= dt)
        except:
            pass
            
    # 按时间倒序
    datas = query.order_by(EnergyMonitor.collect_time.desc()).all()
    
    # 回显参数
    filters = {
        "meter_id": meter_id, "factory_id": factory_id, 
        "data_quality": quality, "start_time": start_time
    }
    
    return render_template('monitor_data.html', monitor_datas=datas, factories=factories, filters=filters)

# --- 3. 峰谷能耗报表 ---
@energy_bp.route('/peak_valley')
def peak_valley():
    factories = [f.factory_id for f in FactoryArea.query.all()]
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('peak_valley.html', factories=factories, today_date=today)

# ================= API 接口部分 =================

@energy_bp.route('/api/meter/add', methods=['POST'])
def add_meter():
    try:
        data = request.form
        # 检查厂区是否存在，如果不存在则默认指定一个(为了演示稳健性)
        # 实际应从前端下拉框选择
        factory = FactoryArea.query.first()
        if not factory:
            return error_resp("请先创建厂区信息")
            
        new_meter = EnergyMeter(
            meter_id=data['meter_id'],
            factory_id=factory.factory_id, # 暂时默认关联第一个厂区
            energy_type=data['energy_type'],
            install_location=data['install_location'],
            pipe_spec=data['pipe_spec'],
            comm_protocol=data['comm_protocol'],
            run_status=data['run_status'],
            calib_cycle=int(data['calib_cycle']),
            manufacturer=data['manufacturer']
        )
        db.session.add(new_meter)
        db.session.commit()
        return success_resp("添加成功")
    except Exception as e:
        db.session.rollback()
        return error_resp(str(e))

@energy_bp.route('/api/meter/update', methods=['POST'])
def update_meter():
    try:
        data = request.form
        meter = EnergyMeter.query.get(data['meter_id'])
        if not meter:
            return error_resp("设备不存在")
            
        meter.energy_type = data['energy_type']
        meter.install_location = data['install_location']
        meter.pipe_spec = data['pipe_spec']
        meter.comm_protocol = data['comm_protocol']
        meter.run_status = data['run_status']
        meter.calib_cycle = int(data['calib_cycle'])
        meter.manufacturer = data['manufacturer']
        
        db.session.commit()
        return success_resp("更新成功")
    except Exception as e:
        return error_resp(str(e))

@energy_bp.route('/api/meter/delete', methods=['POST'])
def delete_meter():
    try:
        meter_id = request.form.get('meter_id')
        meter = EnergyMeter.query.get(meter_id)
        if meter:
            db.session.delete(meter)
            db.session.commit()
        return success_resp("删除成功")
    except Exception as e:
        return error_resp("删除失败，可能存在关联数据")

@energy_bp.route('/api/monitor/verify', methods=['POST'])
def verify_data():
    try:
        data_id = request.form.get('data_id')
        item = EnergyMonitor.query.get(data_id)
        if item:
            item.is_verified = True
            db.session.commit()
            return success_resp()
        return error_resp("数据不存在")
    except Exception as e:
        return error_resp(str(e))

@energy_bp.route('/api/monitor/collect', methods=['POST'])
def collect_data():
    # 模拟：插入一条新数据
    import random
    try:
        meter = EnergyMeter.query.first()
        if not meter: return error_resp("无设备")
        
        new_data = EnergyMonitor(
            data_id=f"D{int(datetime.now().timestamp())}",
            meter_id=meter.meter_id,
            collect_time=datetime.now(),
            energy_value=round(random.uniform(10, 500), 2),
            unit="kWh" if meter.energy_type=="电" else "m³",
            data_quality=random.choice(["优", "良", "中", "差"]),
            factory_id=meter.factory_id,
            is_verified=False
        )
        db.session.add(new_data)
        db.session.commit()
        return success_resp("采集成功")
    except Exception as e:
        return error_resp(str(e))

@energy_bp.route('/api/report/peak_valley', methods=['GET'])
def get_peak_valley_data():
    factory_id = request.args.get('factory_id')
    date_str = request.args.get('date')
    e_type = request.args.get('energy_type')
    
    query = PeakValleyEnergy.query
    
    if factory_id and factory_id != 'all':
        query = query.filter_by(factory_id=factory_id)
    if date_str:
        # 字符串转日期对象
        d = datetime.strptime(date_str, '%Y-%m-%d').date()
        query = query.filter_by(stat_date=d)
    if e_type:
        query = query.filter_by(energy_type=e_type)
        
    # 聚合统计
    stats = query.with_entities(
        func.sum(PeakValleyEnergy.peak_energy).label('sharp'),
        func.sum(PeakValleyEnergy.high_energy).label('peak'),
        func.sum(PeakValleyEnergy.flat_energy).label('flat'),
        func.sum(PeakValleyEnergy.valley_energy).label('valley'),
        func.sum(PeakValleyEnergy.total_energy).label('total'),
        func.sum(PeakValleyEnergy.energy_cost).label('cost')
    ).first()
    
    # 防止 None
    def safe_val(v): return round(v, 2) if v else 0
    
    total = safe_val(stats.total)
    peak_part = safe_val(stats.sharp) + safe_val(stats.peak)
    ratio = round((peak_part / total * 100), 2) if total > 0 else 0
    
    data = {
        "sharp": safe_val(stats.sharp),
        "peak": safe_val(stats.peak),
        "flat": safe_val(stats.flat),
        "valley": safe_val(stats.valley),
        "total_usage": total,
        "total_cost": safe_val(stats.cost),
        "peak_ratio": ratio
    }
    
    return success_resp(data=data)