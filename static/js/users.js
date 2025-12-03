// User Management
const userSearch = document.getElementById('user-search');
const userTableBody = document.getElementById('user-table-body');
const userPageInfo = document.getElementById('user-page-info');
const prevUserPage = document.getElementById('prev-user-page');
const nextUserPage = document.getElementById('next-user-page');

let userCurrentPage = 1;
const userRowsPerPage = 10;

function fetchUsers(page = 1, searchQuery = '') {
    const url = `/admin/get_users?page=${page}&per_page=${userRowsPerPage}&search=${searchQuery}`;
    fetch(url)
        .then(handleResponse)
        .then(data => {
            renderUserTable(data);
        })
        .catch(error => console.error('Error fetching users:', error));
}

function renderUserTable(data) {
    userTableBody.innerHTML = '';
    data.users.forEach(user => {
        userTableBody.innerHTML += `
            <tr>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                <td>${user.video_count || 0}</td>
                <td>
                    <span class="status-badge ${user.is_admin ? 'status-admin' : 'status-active'}">
                        ${user.is_admin ? 'Admin' : 'Active'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-primary btn-sm view-user" data-id="${user.id}">View</button>
                    <button class="btn btn-danger btn-sm delete-user" data-id="${user.id}">Delete</button>
                </td>
            </tr>
        `;
    });

    const totalPages = Math.ceil(data.total / userRowsPerPage);
    userPageInfo.textContent = `Page ${data.page} of ${totalPages}`;
    prevUserPage.disabled = data.page === 1;
    nextUserPage.disabled = data.page === totalPages;
    userCurrentPage = data.page;
}

userSearch.addEventListener('input', () => {
    fetchUsers(1, userSearch.value);
});
prevUserPage.addEventListener('click', () => {
    if (userCurrentPage > 1) {
        fetchUsers(userCurrentPage - 1, userSearch.value);
    }
});
nextUserPage.addEventListener('click', () => {
    fetchUsers(userCurrentPage + 1, userSearch.value);
});

fetchUsers();

// View user buttons using event delegation
userTableBody.addEventListener('click', function(e) {
    if (e.target.classList.contains('view-user')) {
        const userId = e.target.getAttribute('data-id');
        fetch(`/admin/users/${userId}`)
            .then(handleResponse)
            .then(data => {
                populateUserDetailModal(data);
            })
            .catch(error => {
                alert(error.message);
                console.error('Error fetching user details:', error);
            });
    }
});

function populateUserDetailModal(user) {
    document.querySelector('.user-detail-content').innerHTML = `
        <div class="user-detail-header">
            <div class="user-avatar">
                <i class="fas fa-user-circle"></i>
            </div>
            <div class="user-info">
                <h4>${user.name}</h4>
                <p>${user.email}</p>
            </div>
        </div>
        <div class="user-detail-stats">
            <div class="stat">
                <span class="stat-value">${user.video_count || 0}</span>
                <span class="stat-label">Videos Created</span>
            </div>
            <div class="stat">
                <span class="stat-value">${user.is_paid ? 'Paid' : 'Free'}</span>
                <span class="stat-label">Subscription</span>
            </div>
            <div class="stat">
                <span class="stat-value">${new Date(user.created_at).toLocaleDateString()}</span>
                <span class="stat-label">Joined</span>
            </div>
        </div>
        <div class="user-detail-actions">
            <button class="btn btn-sm btn-danger" id="reset-password-btn" data-id="${user.id}">Reset Password</button>
            <button class="btn btn-sm btn-secondary" id="login-as-user-btn" data-id="${user.id}">Login as User</button>
        </div>
    `;
    openModal('user-detail-modal');
}

document.querySelector('.user-detail-content').addEventListener('click', function(e) {
    if (e.target.id === 'reset-password-btn') {
        const userId = e.target.getAttribute('data-id');
        document.getElementById('reset-password-user-id').value = userId;
        openModal('reset-password-modal');
    } else if (e.target.id === 'login-as-user-btn') {
        const userId = e.target.getAttribute('data-id');
        window.location.href = `/admin/login_as/${userId}`;
    }
});

document.getElementById('submit-reset-password').addEventListener('click', function() {
    const userId = document.getElementById('reset-password-user-id').value;
    const newPassword = document.getElementById('new-password').value;
    if (newPassword) {
        fetch(`/admin/users/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: newPassword })
        })
        .then(handleResponse)
        .then(data => {
                showInfoModal('Success', data.message);
            closeModal('reset-password-modal');
        })
        .catch(error => {
                showInfoModal('Error', error.message);
            console.error('Error resetting password:', error);
        });
    }
});

document.getElementById('edit-user-btn').addEventListener('click', function() {
    const userId = document.querySelector('#reset-password-btn').getAttribute('data-id');
    fetch(`/admin/users/${userId}`)
        .then(handleResponse)
        .then(data => {
            document.getElementById('edit-user-id').value = data.id;
            document.getElementById('edit-user-name').value = data.name;
            document.getElementById('edit-user-email').value = data.email;
            closeModal('user-detail-modal');
            openModal('edit-user-modal');
        })
        .catch(error => {
            alert(error.message);
            console.error('Error fetching user for edit:', error);
        });
});

document.getElementById('submit-edit-user').addEventListener('click', function() {
    const userId = document.getElementById('edit-user-id').value;
    const name = document.getElementById('edit-user-name').value;
    const email = document.getElementById('edit-user-email').value;

    fetch(`/admin/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, email: email })
    })
    .then(handleResponse)
    .then(data => {
        showInfoModal('Success', data.message);
        closeModal('edit-user-modal');
        fetchUsers(userCurrentPage, userSearch.value);
    })
    .catch(error => {
        showInfoModal('Error', error.message);
        console.error('Error editing user:', error);
    });
});

// Add User
const addUserForm = document.getElementById('add-user-form');
const submitNewUser = document.getElementById('submit-new-user');

submitNewUser.addEventListener('click', () => {
    const name = document.getElementById('new-user-name').value;
    const email = document.getElementById('new-user-email').value;
    const password = document.getElementById('new-user-password').value;
    const role = document.getElementById('new-user-role').value;

    fetch('/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: name,
            email: email,
            password: password,
            is_admin: role === 'admin'
        })
    })
    .then(handleResponse)
    .then(data => {
        closeModal('add-user-modal');
        addUserForm.reset();
        fetchUsers(); // Refresh the table
        showInfoModal('Success', 'User added successfully');
    })
    .catch(error => {
        showInfoModal('Error', `Error: ${error.message}`);
        console.error('Error adding user:', error);
    });
});

// Delete User
userTableBody.addEventListener('click', function(e) {
    if (e.target.classList.contains('delete-user')) {
        const userId = e.target.getAttribute('data-id');
        showConfirmationModal('Delete User', `Are you sure you want to delete user ${userId}?`, () => {
            fetch(`/admin/users/${userId}`, { method: 'DELETE' })
            .then(handleResponse)
            .then(data => {
                fetchUsers(); // Refresh the table
                // Using a custom alert modal if available, otherwise fallback to browser alert
                if (window.showInfoModal) {
                    showInfoModal('Success', 'User deleted successfully.');
                } else {
                    alert('User deleted successfully');
                }
            })
            .catch(error => {
                if (window.showInfoModal) {
                    showInfoModal('Error', `Error: ${error.message}`);
                } else {
                    alert(`Error: ${error.message}`);
                }
                console.error('Error deleting user:', error);
            });
        });
    }
});
