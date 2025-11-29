function updateDashboard() {
    fetch('/admin/dashboard_data')
        .then(handleResponse)
        .then(data => {
            // Update stats
            document.querySelector('.stat-card h3').textContent = data.total_users;
            document.querySelectorAll('.stat-card h3')[1].textContent = data.total_videos;

            // Update activity list
            const activityList = document.getElementById('activity-list');
            activityList.innerHTML = '';
            data.recent_activity.forEach(item => {
                const iconClass = {
                    user: 'fa-user-plus',
                    video: 'fa-video',
                    payment: 'fa-dollar-sign'
                }[item.activity_type];

                activityList.innerHTML += `
                    <div class="activity-item">
                        <i class="fas ${iconClass}"></i>
                        <div class="activity-content">
                            <p>${item.message}</p>
                            <span>${new Date(item.created_at).toLocaleString()}</span>
                        </div>
                    </div>
                `;
            });

            // Update system metrics
            document.getElementById('cpu-usage').textContent = `${data.system_metrics.cpu_usage.toFixed(1)}%`;
            document.getElementById('memory-usage').textContent = `${data.system_metrics.memory_usage.toFixed(1)}%`;
            document.getElementById('disk-usage').textContent = `${data.system_metrics.disk_usage.toFixed(1)}%`;
        })
        .catch(error => console.error('Error fetching dashboard data:', error));
}

// Initial load and periodic refresh
updateDashboard();
setInterval(updateDashboard, 30000); // Refresh every 30 seconds
