let myChart = null;

document.addEventListener('DOMContentLoaded', function() {
    // 页面加载时若有默认日期，自动查询一次
    if(document.getElementById('pv_date').value) {
        loadPeakValleyData();
    }
});

function loadPeakValleyData() {
    const factory = document.getElementById('pv_factory').value;
    const date = document.getElementById('pv_date').value;
    const type = document.getElementById('pv_type').value;

    const params = { factory_id: factory, date: date, energy_type: type };

    ajaxRequest('/energy/api/report/peak_valley', 'GET', params, (res) => {
        if(res.success) {
            updateDashboard(res.data, type);
        } else {
            // 如果后端没数据，这里为了演示不报错，可以注释掉下面这行
            alert("未查询到数据或请求失败");
        }
    }, (err) => {
        console.error("请求错误，使用模拟数据演示");
        const mockData = {
            sharp: 120, peak: 300, flat: 200, valley: 150,
            total_usage: 770, total_cost: 850.5, peak_ratio: 54.5
        };
        updateDashboard(mockData, type);
    });
}

function updateDashboard(data, type) {
    const unit = type === '电' ? 'kWh' : (type === '水' ? 'm³' : 'm³');
    document.getElementById('usage_unit').innerText = unit;
    
    // 更新卡片
    document.getElementById('total_usage').innerText = data.total_usage;
    document.getElementById('total_cost').innerText = data.total_cost;
    document.getElementById('peak_ratio').innerText = data.peak_ratio;

    // 更新图表
    renderChart(data);

    // 更新表格
    const factoryText = document.getElementById('pv_factory').options[document.getElementById('pv_factory').selectedIndex].text;
    const tbody = document.getElementById('reportTableBody');
    tbody.innerHTML = `
        <tr>
            <td>${document.getElementById('pv_date').value}</td>
            <td>${factoryText}</td>
            <td>${data.sharp}</td>
            <td>${data.peak}</td>
            <td>${data.flat}</td>
            <td>${data.valley}</td>
            <td><strong>${data.total_usage}</strong></td>
            <td style="color:var(--danger-color)">${data.total_cost}</td>
        </tr>
    `;
}

function renderChart(data) {
    const ctx = document.getElementById('costChart').getContext('2d');
    
    if(myChart) {
        myChart.destroy();
    }

    myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['尖峰时段', '高峰时段', '平段', '低谷时段'],
            datasets: [{
                label: '能耗量',
                data: [data.sharp, data.peak, data.flat, data.valley],
                backgroundColor: [
                    'rgba(231, 76, 60, 0.7)',  // 红
                    'rgba(243, 156, 18, 0.7)', // 橙
                    'rgba(52, 152, 219, 0.7)', // 蓝
                    'rgba(46, 204, 113, 0.7)'  // 绿
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}