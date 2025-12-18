from datetime import datetime, time
from config import Config

def get_period_type(collect_time: datetime) -> str:
    """
    根据采集时间判断峰谷时段类型
    :param collect_time: 采集时间（datetime对象）
    :return: 时段类型（peak=尖峰, high=高峰, flat=平段, valley=低谷）
    """
    collect_hour = collect_time.hour
    collect_minute = collect_time.minute
    current_time = time(collect_hour, collect_minute)
    
    # 尖峰时段：10:00-12:00 或 16:00-18:00
    if (time(10, 0) <= current_time < time(12, 0)) or (time(16, 0) <= current_time < time(18, 0)):
        return "peak"
    # 高峰时段：8:00-10:00 或 12:00-16:00 或 18:00-22:00
    elif (time(8, 0) <= current_time < time(10, 0)) or (time(12, 0) <= current_time < time(16, 0)) or (time(18, 0) <= current_time < time(22, 0)):
        return "high"
    # 平段时段：6:00-8:00 或 22:00-24:00
    elif (time(6, 0) <= current_time < time(8, 0)) or (time(22, 0) <= current_time <= time(23, 59)):
        return "flat"
    # 低谷时段：00:00-6:00
    else:
        return "valley"

def generate_data_id(prefix: str) -> str:
    """
    生成唯一数据编号（前缀+时间戳）
    :param prefix: 前缀（如meter=设备, monitor=监测, peak=峰谷）
    :return: 唯一编号（如monitor_20250101120000001）
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:15]  # 时间戳（精确到毫秒）
    return f"{prefix}_{timestamp}"

def verify_energy_value(energy_type: str, value: float) -> bool:
    """
    验证能耗值合法性（非负，且符合能源类型常识）
    :param energy_type: 能源类型（水/蒸汽/天然气）
    :param value: 能耗值
    :return: 合法返回True，否则False
    """
    if value < 0:
        return False
    # 简单阈值校验（可根据实际调整）
    max_values = {"水": 1000, "蒸汽": 500, "天然气": 2000}  # 单条数据最大能耗值
    return value <= max_values.get(energy_type, 10000)