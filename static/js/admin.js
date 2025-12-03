document.addEventListener('DOMContentLoaded', function() {
    // Centralized error handling for fetch
    window.handleResponse = function(response) {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.message || 'Something went wrong') });
        }
        return response.json();
    }

    // Admin navigation
    const adminNavLinks = document.querySelectorAll('.admin-nav-link');
    const adminSections = document.querySelectorAll('.admin-section');

    adminNavLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetSection = this.getAttribute('data-section');

            // Update active nav link
            adminNavLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            // Show corresponding section
            adminSections.forEach(section => {
                section.classList.remove('active');
                if (section.classList.contains(`${targetSection}-section`)) {
                    section.classList.add('active');
                }
            });
        });
    });

    // Modal functionality
    const modals = document.querySelectorAll('.modal');
    const modalCloseButtons = document.querySelectorAll('.modal-close');

    window.openModal = function(modalId) {
        document.getElementById(modalId).style.display = 'block';
    }

    window.closeModal = function(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    modalCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            modal.style.display = 'none';
        });
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Add user button
    const addUserBtn = document.getElementById('add-user-btn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', function() {
            openModal('add-user-modal');
        });
    }

    // Confirmation Modal Logic
    const confirmActionBtn = document.getElementById('confirm-action-btn');
    let confirmCallback = null;

    window.showConfirmationModal = function(title, message, callback) {
        document.getElementById('confirmation-title').textContent = title;
        document.getElementById('confirmation-message').textContent = message;
        confirmCallback = callback;
        openModal('confirmation-modal');
    }

    confirmActionBtn.addEventListener('click', () => {
        if (confirmCallback) {
            confirmCallback();
        }
        closeModal('confirmation-modal');
    });

    // Info Modal Logic
    window.showInfoModal = function(title, message) {
        document.getElementById('info-title').textContent = title;
        document.getElementById('info-message').textContent = message;
        openModal('info-modal');
    }
});
