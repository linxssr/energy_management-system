from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from app import db
from models import EnergyMeter, EnergyMonitor, PeakValleyEnergy
from utils.common_utils import get_period_type, generate_data_id, verify_energy_value
from config import Config
from datetime import datetime, date, time

class EnergyService:
    # -------------------------- 1. 能耗计量设备管理 --------------------------
    @staticmethod
    def get_all_meters(energy_type: str = None, run_status: str = None) -> list:
        """查询所有计量设备（支持按能源类型、运行状态筛选）"""
        query = EnergyMeter.query
        if energy_type:
            query = query.filter_by(energy_type=energy_type)
        if run_status:
            query = query.filter_by(run_status=run_status)
        return query.all()
    
    @staticmethod
    def get_meter_by_id(meter_id: str) -> EnergyMeter:
        """根据设备编号查询单个设备"""
        return EnergyMeter.query.filter_by(meter_id=meter_id).first()
    
    @staticmethod
    def add_meter(meter_data: dict) -> tuple[bool, str]:
        """新增能耗计量设备"""
        try:
            # 验证设备编号是否已存在
            if EnergyMeter.query.filter_by(meter_id=meter_data["meter_id"]).first():
                return False, f"设备编号{meter_data['meter_id']}已存在！"
            # 验证能源类型合法性
            if meter_data["energy_type"] not in ["水", "蒸汽", "天然气"]:
                return False, "能源类型必须是'水'、'蒸汽'或'天然气'！"
            # 创建设备对象
            new_meter = EnergyMeter(
                meter_id=meter_data["meter_id"],
                energy_type=meter_data["energy_type"],
                install_location=meter_data["install_location"],
                pipe_spec=meter_data.get("pipe_spec", ""),
                comm_protocol=meter_data["comm_protocol"],
                run_status=meter_data.get("run_status", "正常"),
                calib_cycle=meter_data["calib_cycle"],
                manufacturer=meter_data.get("manufacturer", "")
            )
            db.session.add(new_meter)
            db.session.commit()
            return True, "设备新增成功！"
        except Exception as e:
            db.session.rollback()
            return False, f"新增失败：{str(e)}"
    
    @staticmethod
    def update_meter(meter_id: str, update_data: dict) -> tuple[bool, str]:
        """修改能耗计量设备信息"""
        try:
            meter = EnergyMeter.query.filter_by(meter_id=meter_id).first()
            if not meter:
                return False, f"设备编号{meter_id}不存在！"
            # 批量更新字段（仅更新传入的非空字段）
            for key, value in update_data.items():
                if hasattr(meter, key) and value is not None:
                    setattr(meter, key, value)
            db.session.commit()
            return True, "设备更新成功！"
        except Exception as e:
            db.session.rollback()
            return False, f"更新失败：{str(e)}"
    
    @staticmethod
    def delete_meter(meter_id: str) -> tuple[bool, str]:
        """删除能耗计量设备（需先删除关联的监测数据）"""
        try:
            meter = EnergyMeter.query.filter_by(meter_id=meter_id).first()
            if not meter:
                return False, f"设备编号{meter_id}不存在！"
            # 删除关联的监测数据
            EnergyMonitor.query.filter_by(meter_id=meter_id).delete()
            # 删除设备
            db.session.delete(meter)
            db.session.commit()
            return True, "设备删除成功！"
        except Exception as e:
            db.session.rollback()
            return False, f"删除失败：{str(e)}"
    
    # -------------------------- 2. 能耗监测数据管理 --------------------------
    @staticmethod
    def add_energy_monitor(monitor_data: dict) -> tuple[bool, str]:
        """新增能耗监测数据（含数据质量校验）"""
        try:
            # 验证设备是否存在
            meter = EnergyMeter.query.filter_by(meter_id=monitor_data["meter_id"]).first()
            if not meter:
                return False, f"关联设备{monitor_data['meter_id']}不存在！"
            # 验证能耗值合法性
            if not verify_energy_value(meter.energy_type, monitor_data["energy_value"]):
                return False, f"能耗值{monitor_data['energy_value']}不合法（非负且不超过阈值）！"
            # 生成数据编号
            data_id = generate_data_id("monitor")
            # 自动设置单位（根据能源类型）
            unit_map = {"水": "m³", "蒸汽": "t", "天然气": "m³"}
            unit = unit_map[meter.energy_type]
            # 标记是否需要核实（数据质量为中/差时）
            data_quality = monitor_data.get("data_quality", "良")
            is_verified = False if data_quality in ["中", "差"] else True
            
            # 创建监测数据对象
            new_monitor = EnergyMonitor(
                data_id=data_id,
                meter_id=monitor_data["meter_id"],
                collect_time=datetime.strptime(monitor_data["collect_time"], "%Y-%m-%d %H:%M:%S"),
                energy_value=monitor_data["energy_value"],
                unit=unit,
                data_quality=data_quality,
                factory_id=monitor_data["factory_id"],
                is_verified=is_verified
            )
            db.session.add(new_monitor)
            db.session.commit()
            
            # 自动触发峰谷数据生成（按日统计，当天数据仅生成一次）
            stat_date = new_monitor.collect_time.date()
            if not PeakValleyEnergy.query.filter_by(
                energy_type=meter.energy_type,
                factory_id=monitor_data["factory_id"],
                stat_date=stat_date
            ).first():
                EnergyService.generate_peak_valley_daily(meter.energy_type, monitor_data["factory_id"], stat_date)
            
            return True, f"监测数据新增成功（编号：{data_id}）！"
        except Exception as e:
            db.session.rollback()
            return False, f"新增失败：{str(e)}"
    
    @staticmethod
    def get_monitor_data(filters: dict) -> list:
        """查询能耗监测数据（支持多条件筛选）"""
        query = EnergyMonitor.query.join(EnergyMeter, EnergyMonitor.meter_id == EnergyMeter.meter_id)
        # 筛选条件：设备编号、厂区、时间范围、数据质量
        if filters.get("meter_id"):
            query = query.filter(EnergyMonitor.meter_id == filters["meter_id"])
        if filters.get("factory_id"):
            query = query.filter(EnergyMonitor.factory_id == filters["factory_id"])
        if filters.get("start_time") and filters.get("end_time"):
            start_time = datetime.strptime(filters["start_time"], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(filters["end_time"], "%Y-%m-%d %H:%M:%S")
            query = query.filter(EnergyMonitor.collect_time.between(start_time, end_time))
        if filters.get("data_quality"):
            query = query.filter(EnergyMonitor.data_quality == filters["data_quality"])
        # 按采集时间降序
        return query.order_by(EnergyMonitor.collect_time.desc()).all()
    
    @staticmethod
    def verify_monitor_data(data_id: str) -> tuple[bool, str]:
        """审核监测数据（标记为已核实）"""
        try:
            monitor = EnergyMonitor.query.filter_by(data_id=data_id).first()
            if not monitor:
                return False, f"监测数据{data_id}不存在！"
            monitor.is_verified = True
            db.session.commit()
            return True, "数据审核通过！"
        except Exception as e:
            db.session.rollback()
            return False, f"审核失败：{str(e)}"
    
    # -------------------------- 3. 峰谷能耗报表管理 --------------------------
    @staticmethod
    def generate_peak_valley_daily(energy_type: str, factory_id: str, stat_date: date) -> tuple[bool, str]:
        """生成每日峰谷能耗数据（按文档时段统计）"""
        try:
            # 查询当天该厂区、该能源类型的所有监测数据
            start_time = datetime.combine(stat_date, time(0, 0, 0))
            end_time = datetime.combine(stat_date, time(23, 59, 59))
            monitor_datas = EnergyMonitor.query.filter(
                and_(
                    EnergyMonitor.factory_id == factory_id,
                    EnergyMonitor.collect_time.between(start_time, end_time)
                )
            ).join(EnergyMeter, EnergyMonitor.meter_id == EnergyMeter.meter_id).filter(
                EnergyMeter.energy_type == energy_type
            ).all()
            
            if not monitor_datas:
                return False, f"{stat_date} {factory_id} {energy_type}无监测数据，无法生成峰谷报表！"
            
            # 按时段统计能耗
            peak_energy = 0  # 尖峰
            high_energy = 0  # 高峰
            flat_energy = 0  # 平段
            valley_energy = 0  # 低谷
            
            for data in monitor_datas:
                period_type = get_period_type(data.collect_time)
                if period_type == "peak":
                    peak_energy += data.energy_value
                elif period_type == "high":
                    high_energy += data.energy_value
                elif period_type == "flat":
                    flat_energy += data.energy_value
                elif period_type == "valley":
                    valley_energy += data.energy_value
            
            # 计算总能耗和成本
            total_energy = peak_energy + high_energy + flat_energy + valley_energy
            # 取对应能源类型的电价（此处简化：统一用配置的电价，实际可按能源类型调整）
            price = Config.PEAK_VALLEY_PRICES
            total_cost = (peak_energy * price["peak"]) + (high_energy * price["high"]) + (flat_energy * price["flat"]) + (valley_energy * price["valley"])
            
            # 生成峰谷记录编号
            record_id = generate_data_id("peak")
            # 创建峰谷数据对象
            new_peak_valley = PeakValleyEnergy(
                record_id=record_id,
                energy_type=energy_type,
                factory_id=factory_id,
                stat_date=stat_date,
                peak_energy=round(peak_energy, 2),
                high_energy=round(high_energy, 2),
                flat_energy=round(flat_energy, 2),
                valley_energy=round(valley_energy, 2),
                total_energy=round(total_energy, 2),
                peak_valley_price=round(price["peak"], 2),  # 存储尖峰电价（可扩展为多电价）
                energy_cost=round(total_cost, 2)
            )
            db.session.add(new_peak_valley)
            db.session.commit()
            return True, f"{stat_date} {factory_id} {energy_type}峰谷报表生成成功！"
        except Exception as e:
            db.session.rollback()
            return False, f"报表生成失败：{str(e)}"
    
    @staticmethod
    def get_peak_valley_daily(factory_id: str, stat_date: date, energy_type: str = None) -> list:
        """查询每日峰谷能耗报表"""
        query = PeakValleyEnergy.query.filter(
            and_(
                PeakValleyEnergy.factory_id == factory_id,
                PeakValleyEnergy.stat_date == stat_date
            )
        )
        if energy_type:
            query = query.filter(PeakValleyEnergy.energy_type == energy_type)
        return query.all()
    
    @staticmethod
    def get_high_consumption_factories(stat_date: date, threshold: float = 30) -> list:
        """定位高耗能区域（能耗超平均值{threshold}%的厂区）"""
        try:
            # 计算当天所有厂区的平均能耗（按能源类型分组）
            avg_subquery = db.session.query(
                PeakValleyEnergy.energy_type,
                func.avg(PeakValleyEnergy.total_energy).label("avg_energy")
            ).filter(PeakValleyEnergy.stat_date == stat_date).group_by(PeakValleyEnergy.energy_type).subquery()
            
            # 查询超平均值的厂区
            high_consume = db.session.query(
                PeakValleyEnergy,
                avg_subquery.c.avg_energy
            ).join(
                avg_subquery,
                PeakValleyEnergy.energy_type == avg_subquery.c.energy_type
            ).filter(
                and_(
                    PeakValleyEnergy.stat_date == stat_date,
                    PeakValleyEnergy.total_energy > avg_subquery.c.avg_energy * (1 + threshold / 100)
                )
            ).all()
            
            # 格式化返回结果
            result = []
            for item, avg_energy in high_consume:
                result.append({
                    "factory_id": item.factory_id,
                    "energy_type": item.energy_type,
                    "total_energy": item.total_energy,
                    "avg_energy": round(avg_energy, 2),
                    "exceed_rate": round((item.total_energy - avg_energy) / avg_energy * 100, 2)  # 超平均率
                })
            return result
        except Exception as e:
            return f"查询失败：{str(e)}"