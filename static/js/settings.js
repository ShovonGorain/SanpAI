// System Settings
function fetchSettings() {
    fetch('/admin/settings')
    .then(handleResponse)
    .then(data => {
        document.getElementById('login-attempts').value = data.login_attempts;
        document.getElementById('session-timeout').value = data.session_timeout;
        document.getElementById('video-quality').value = data.video_quality;
    })
    .catch(error => console.error('Error fetching settings:', error));
}

fetchSettings();

document.getElementById('save-security-settings').addEventListener('click', () => {
    const settings = {
        login_attempts: document.getElementById('login-attempts').value,
        session_timeout: document.getElementById('session-timeout').value
    };
    fetch('/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    .then(handleResponse)
    .then(data => {
        showInfoModal('Success', 'Security settings saved.');
    })
    .catch(error => {
        showInfoModal('Error', `Error: ${error.message}`);
        console.error('Error saving security settings:', error);
    });
});

document.getElementById('save-system-settings').addEventListener('click', () => {
    const settings = {
        video_quality: document.getElementById('video-quality').value
    };
    fetch('/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    .then(handleResponse)
    .then(data => {
        showInfoModal('Success', 'System settings saved.');
    })
    .catch(error => {
        showInfoModal('Error', `Error: ${error.message}`);
        console.error('Error saving system settings:', error);
    });
});

const dbFeedback = document.getElementById('db-feedback');

function showDbFeedback(message, isSuccess) {
    dbFeedback.textContent = message;
    dbFeedback.className = `feedback-message ${isSuccess ? 'success' : 'error'}`;
}

document.getElementById('backup-db').addEventListener('click', () => {
    showConfirmationModal('Backup Database', 'Are you sure you want to back up the database?', () => {
        fetch('/admin/database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'backup' })
        })
        .then(handleResponse)
        .then(data => {
            showDbFeedback(data.message, data.success);
        })
        .catch(error => {
            showDbFeedback(error.message, false);
            console.error('Error backing up database:', error);
        });
    });
});

document.getElementById('optimize-db').addEventListener('click', () => {
    showConfirmationModal('Optimize Database', 'Are you sure you want to optimize the database?', () => {
        fetch('/admin/database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'optimize' })
        })
        .then(handleResponse)
        .then(data => {
            showDbFeedback(data.message, data.success);
        })
        .catch(error => {
            showDbFeedback(error.message, false);
            console.error('Error optimizing database:', error);
        });
    });
});

document.getElementById('clear-db').addEventListener('click', () => {
    openModal('clear-all-data-modal');
});

document.getElementById('submit-clear-all-data').addEventListener('click', function() {
    const confirmText = document.getElementById('clear-all-data-confirm').value;
    if (confirmText === 'DELETE') {
        fetch('/admin/database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'clear' })
        })
        .then(handleResponse)
        .then(data => {
            showDbFeedback(data.message, data.success);
            if (data.success) {
                fetchUsers();
                fetchVideos();
                closeModal('clear-all-data-modal');
            }
        })
        .catch(error => {
            showDbFeedback(error.message, false);
            console.error('Error clearing database:', error);
        });
    } else {
        alert('Please type "DELETE" to confirm.');
    }
});

// API key reveal
const revealApiKeyBtn = document.getElementById('reveal-api-key');
if (revealApiKeyBtn) {
    revealApiKeyBtn.addEventListener('click', function() {
        const apiKeyInput = document.getElementById('api-key');
        if (apiKeyInput.type === 'password') {
            // Fetch the API key from the server
            fetch('/admin/api_key')
                .then(handleResponse)
                .then(data => {
                    apiKeyInput.type = 'text';
                    apiKeyInput.value = data.api_key;
                    this.textContent = 'Hide';
                })
                .catch(error => {
                    showInfoModal('Error', 'Could not fetch API key.');
                    console.error('Error fetching API key:', error);
                });
        } else {
            apiKeyInput.type = 'password';
            apiKeyInput.value = '••••••••••••••••';
            this.textContent = 'Reveal';
        }
    });
}
