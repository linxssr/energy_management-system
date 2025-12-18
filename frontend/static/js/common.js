/**
 * 通用AJAX请求函数
 * @param {string} url - 请求地址
 * @param {string} method - 请求方法（GET/POST）
 * @param {object} data - 请求数据
 * @param {function} successCallback - 成功回调
 * @param {function} errorCallback - 失败回调
 */
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    
    // POST请求设置请求头
    if (method.toUpperCase() === "POST") {
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    }
    
    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const response = JSON.parse(xhr.responseText);
            successCallback && successCallback(response);
        } else {
            errorCallback && errorCallback(`请求失败（状态码：${xhr.status}）`);
            alert(`请求失败：${xhr.statusText}`);
        }
    };
    
    xhr.onerror = function() {
        errorCallback && errorCallback("网络错误");
        alert("网络错误，请重试！");
    };
    
    // 处理请求数据（GET拼接在URL，POST放在请求体）
    if (method.toUpperCase() === "GET") {
        const params = new URLSearchParams(data).toString();
        xhr.send(params ? `?${params}` : null);
    } else {
        const params = new URLSearchParams(data).toString();
        xhr.send(params);
    }
}

/**
 * 弹窗控制函数
 * @param {string} modalId - 弹窗ID
 * @param {boolean} show - 显示/隐藏（true/false）
 */
function controlModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (show) {
        modal.classList.add("show");
    } else {
        modal.classList.remove("show");
    }
}

/**
 * 格式化日期时间（YYYY-MM-DD HH:MM:SS）
 * @param {Date} date - 日期对象
 * @return {string} 格式化后的字符串
 */
function formatDateTime(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");
    const second = String(date.getSeconds()).padStart(2, "0");
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

/**
 * 格式化日期（YYYY-MM-DD）
 * @param {Date} date - 日期对象
 * @return {string} 格式化后的字符串
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

/**
 * 刷新当前页面
 */
function refreshPage() {
    window.location.reload();
}