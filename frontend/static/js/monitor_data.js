function filterMonitorData() {
    const meter_id = document.getElementById('s_meter_id').value;
    const factory_id = document.getElementById('s_factory_id').value;
    const data_quality = document.getElementById('s_data_quality').value;
    const start_time = document.getElementById('s_start_time').value;
    
    const params = new URLSearchParams({
        meter_id: meter_id,
        factory_id: factory_id,
        data_quality: data_quality,
        start_time: start_time
    });
    
    window.location.href = `/energy/monitor_data?${params.toString()}`;
}

function verifyData(dataId) {
    if(confirm(`确认该条数据（ID: ${dataId}）已通过人工核查吗？`)) {
        ajaxRequest('/energy/api/monitor/verify', 'POST', { data_id: dataId }, (res) => {
            if(res.success) {
                alert("审核成功");
                refreshPage();
            } else {
                alert("操作失败：" + res.message);
            }
        });
    }
}

function simulateCollection() {
    ajaxRequest('/energy/api/monitor/collect', 'POST', {}, (res) => {
        alert("模拟采集指令已发送，页面将自动刷新");
        setTimeout(refreshPage, 1000);
    });
}