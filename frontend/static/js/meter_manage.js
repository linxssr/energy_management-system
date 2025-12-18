function searchMeters() {
    const type = document.getElementById('filter_energy_type').value;
    const status = document.getElementById('filter_run_status').value;
    window.location.href = `/energy/meter_manage?energy_type=${type}&run_status=${status}`;
}

function resetMeterFilter() {
    window.location.href = '/energy/meter_manage';
}

function showAddMeterModal() {
    document.getElementById('modalTitle').innerText = "新增能耗计量设备";
    document.getElementById('meterForm').reset();
    document.getElementById('is_edit').value = "false";
    document.getElementById('meter_id').disabled = false;
    controlModal('meterModal', true);
}

// 修复点：从按钮的 data-meter 属性获取数据
function prepareEditMeter(button) {
    const meterData = JSON.parse(button.getAttribute('data-meter'));
    
    document.getElementById('modalTitle').innerText = "编辑能耗计量设备";
    document.getElementById('is_edit').value = "true";
    
    document.getElementById('meter_id').value = meterData.meter_id;
    document.getElementById('meter_id').disabled = true; 
    document.getElementById('energy_type').value = meterData.energy_type;
    document.getElementById('install_location').value = meterData.install_location;
    document.getElementById('pipe_spec').value = meterData.pipe_spec || '';
    document.getElementById('comm_protocol').value = meterData.comm_protocol;
    document.getElementById('run_status').value = meterData.run_status;
    document.getElementById('calib_cycle').value = meterData.calib_cycle;
    document.getElementById('manufacturer').value = meterData.manufacturer || '';
    
    controlModal('meterModal', true);
}

function submitMeter() {
    const isEdit = document.getElementById('is_edit').value === "true";
    const data = {
        meter_id: document.getElementById('meter_id').value,
        energy_type: document.getElementById('energy_type').value,
        install_location: document.getElementById('install_location').value,
        pipe_spec: document.getElementById('pipe_spec').value,
        comm_protocol: document.getElementById('comm_protocol').value,
        run_status: document.getElementById('run_status').value,
        calib_cycle: document.getElementById('calib_cycle').value,
        manufacturer: document.getElementById('manufacturer').value
    };

    if(!data.meter_id) { alert("请输入设备编号"); return; }

    const url = isEdit ? '/energy/api/meter/update' : '/energy/api/meter/add';
    
    ajaxRequest(url, 'POST', data, (res) => {
        if(res.success) {
            alert("保存成功");
            refreshPage();
        } else {
            alert("保存失败：" + res.message);
        }
    });
}

function deleteMeter(meterId) {
    if(confirm("确定要删除该设备吗？此操作不可恢复。")) {
        ajaxRequest('/energy/api/meter/delete', 'POST', { meter_id: meterId }, (res) => {
            if(res.success) {
                alert("删除成功");
                refreshPage();
            } else {
                alert("删除失败：" + res.message);
            }
        });
    }
}