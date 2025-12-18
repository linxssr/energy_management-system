from datetime import datetime
from database import db

class EnergyMeter(db.Model):
    """能耗计量设备信息表"""
    __tablename__ = "energy_meter"
    
    meter_id = db.Column(db.String(20), primary_key=True, comment="设备编号")
    factory_id = db.Column(db.String(20), db.ForeignKey("factory_area.factory_id"), nullable=False, comment="所属厂区编号")
    energy_type = db.Column(db.Enum("水", "蒸汽", "天然气"), nullable=False, comment="能源类型")
    install_location = db.Column(db.String(100), nullable=False, comment="安装位置")
    pipe_spec = db.Column(db.String(20), comment="管径规格")
    comm_protocol = db.Column(db.Enum("RS485", "Lora"), nullable=False, comment="通讯协议")
    run_status = db.Column(db.Enum("正常", "故障"), default="正常", comment="运行状态")
    calib_cycle = db.Column(db.Integer, nullable=False, comment="校准周期")
    manufacturer = db.Column(db.String(50), comment="生产厂家")
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    monitor_datas = db.relationship("EnergyMonitor", backref="meter", lazy=True)

    # 【新增】序列化方法：将数据库对象转为字典，解决 JSON 报错
    def to_dict(self):
        return {
            "meter_id": self.meter_id,
            "factory_id": self.factory_id,
            "energy_type": self.energy_type,
            "install_location": self.install_location,
            "pipe_spec": self.pipe_spec,
            "comm_protocol": self.comm_protocol,
            "run_status": self.run_status,
            "calib_cycle": self.calib_cycle,
            "manufacturer": self.manufacturer
        }

class EnergyMonitor(db.Model):
    __tablename__ = "energy_monitor"
    data_id = db.Column(db.String(30), primary_key=True)
    meter_id = db.Column(db.String(20), db.ForeignKey("energy_meter.meter_id"), nullable=False)
    collect_time = db.Column(db.DateTime, nullable=False)
    energy_value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    data_quality = db.Column(db.Enum("优", "良", "中", "差"), default="良")
    factory_id = db.Column(db.String(20), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    peak_valley = db.relationship("PeakValleyEnergy", backref="monitor_data", lazy=True, uselist=False)

    # 【新增】序列化方法
    def to_dict(self):
        return {
            "data_id": self.data_id,
            "meter_id": self.meter_id,
            "collect_time": self.collect_time.strftime("%Y-%m-%d %H:%M:%S") if self.collect_time else None,
            "energy_value": self.energy_value,
            "unit": self.unit,
            "data_quality": self.data_quality,
            "factory_id": self.factory_id,
            "is_verified": self.is_verified
        }

class PeakValleyEnergy(db.Model):
    __tablename__ = "peak_valley_energy"
    record_id = db.Column(db.String(30), primary_key=True)
    energy_type = db.Column(db.Enum("水", "蒸汽", "天然气"), nullable=False)
    factory_id = db.Column(db.String(20), nullable=False)
    stat_date = db.Column(db.Date, nullable=False)
    peak_energy = db.Column(db.Float, default=0)
    high_energy = db.Column(db.Float, default=0)
    flat_energy = db.Column(db.Float, default=0)
    valley_energy = db.Column(db.Float, default=0)
    total_energy = db.Column(db.Float, nullable=False)
    peak_valley_price = db.Column(db.Float, nullable=False)
    energy_cost = db.Column(db.Float, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    monitor_data_id = db.Column(db.String(30), db.ForeignKey("energy_monitor.data_id"))

class FactoryArea(db.Model):
    __tablename__ = "factory_area"
    factory_id = db.Column(db.String(20), primary_key=True)
    factory_name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200))
    manager = db.Column(db.String(50))
    create_time = db.Column(db.DateTime, default=datetime.now)
    meters = db.relationship("EnergyMeter", backref="factory", lazy=True)