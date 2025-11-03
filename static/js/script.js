// Initialize particles.js
document.addEventListener('DOMContentLoaded', function () {
    // Initialize particles if the element exists
    if (document.getElementById('particles-js')) {
        particlesJS('particles-js', {
            particles: {
                number: {
                    value: 80,
                    density: {
                        enable: true,
                        value_area: 800
                    }
                },
                color: {
                    value: "#8a2be2"
                },
                shape: {
                    type: "circle",
                    stroke: {
                        width: 0,
                        color: "#000000"
                    }
                },
                opacity: {
                    value: 0.5,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 1,
                        opacity_min: 0.1,
                        sync: false
                    }
                },
                size: {
                    value: 15,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 10,
                        size_min: 0.1,
                        sync: false
                    }
                },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: "#5e17eb",
                    opacity: 0.4,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 4,
                    direction: "none",
                    random: true,
                    straight: false,
                    out_mode: "out",
                    bounce: false,
                    attract: {
                        enable: false,
                        rotateX: 600,
                        rotateY: 1200
                    }
                }
            },
            interactivity: {
                detect_on: "canvas",
                events: {
                    onhover: {
                        enable: true,
                        mode: "grab"
                    },
                    onclick: {
                        enable: true,
                        mode: "push"
                    },
                    resize: true
                },
                modes: {
                    grab: {
                        distance: 140,
                        line_linked: {
                            opacity: 1
                        }
                    },
                    push: {
                        particles_nb: 14
                    }
                }
            },
            retina_detect: true
        });
    }

    // Section navigation
    const sections = document.querySelectorAll('.section');
    const navLinks = document.querySelectorAll('.nav-links a');

    // Show home section by default if it exists
    const homeSection = document.getElementById('home');
    if (homeSection) {
        homeSection.classList.add('active');
    }

    // Handle navigation clicks
    if (navLinks.length > 0) {
        navLinks.forEach(link => {
            link.addEventListener('click', function (e) {
                e.preventDefault();

                const targetSection = this.getAttribute('data-section');

                // Hide all sections
                sections.forEach(section => {
                    section.classList.remove('active');
                });

                // Show target section
                document.getElementById(targetSection).classList.add('active');

                // Scroll to top
                window.scrollTo(0, 0);
            });
        });
    }

    // Simple animation observer
    const animatedElements = document.querySelectorAll('.animated');

    // Trigger animations on scroll
    if (animatedElements.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                    observer.unobserve(entry.target);
                }
            });
        });

        animatedElements.forEach(el => {
            observer.observe(el);
        });
    }

    // Music selection
    const musicOptions = document.querySelectorAll('.music-option');
    musicOptions.forEach(option => {
        option.addEventListener('click', () => {
            musicOptions.forEach(o => o.classList.remove('active'));
            option.classList.add('active');
        });
    });

    // Upload area interaction
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('click', () => {
            // Create a file input element
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.multiple = true;
            fileInput.accept = 'image/*';
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    // Show file names or count
                    const fileCount = e.target.files.length;
                    uploadArea.innerHTML = `
                        <i class="fas fa-check-circle"></i>
                        <h3>${fileCount} file${fileCount > 1 ? 's' : ''} selected</h3>
                        <p>Click to change selection</p>
                    `;
                    
                    // Store files for later use
                    uploadArea.files = e.target.files;
                }
            });
            
            fileInput.click();
        });
    }

    // Authentication functionality
    const authTabs = document.querySelectorAll('.auth-tab');
    const authForms = document.querySelectorAll('.auth-form');

    if (authTabs.length > 0) {
        authTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('data-tab');
                
                // Update active tab
                authTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Show corresponding form
                authForms.forEach(form => {
                    form.classList.remove('active');
                    if (form.id === `${targetTab}-form`) {
                        form.classList.add('active');
                    }
                });
            });
        });

        // Switch between login and register forms
        const goToRegister = document.getElementById('go-to-register');
        const goToLogin = document.getElementById('go-to-login');
        
        if (goToRegister) {
            goToRegister.addEventListener('click', (e) => {
                e.preventDefault();
                authTabs[1].click();
            });
        }
        
        if (goToLogin) {
            goToLogin.addEventListener('click', (e) => {
                e.preventDefault();
                authTabs[0].click();
            });
        }
    }

    // Password visibility toggle
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', () => {
            const input = button.previousElementSibling;
            const icon = button.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // Form validation
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            if (!validateLoginForm()) {
                e.preventDefault();
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            if (!validateRegisterForm()) {
                e.preventDefault();
            }
        });
    }

    // Video generation
    const generateButtons = document.querySelectorAll('.generate-btn');
    generateButtons.forEach(button => {
        button.addEventListener('click', generateVideo);
    });

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '1';
            message.style.transition = 'opacity 0.5s ease';
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });
});

// Form validation functions
function validateLoginForm() {
    let isValid = true;
    const email = document.getElementById('login-email');
    const password = document.getElementById('login-password');
    const emailError = document.getElementById('login-email-error');
    const passwordError = document.getElementById('login-password-error');

    // Reset errors
    if (email) email.classList.remove('error');
    if (password) password.classList.remove('error');
    if (emailError) emailError.style.display = 'none';
    if (passwordError) passwordError.style.display = 'none';

    // Validate email
    if (email && (!email.value || !isValidEmail(email.value))) {
        email.classList.add('error');
        if (emailError) emailError.style.display = 'block';
        isValid = false;
    }

    // Validate password
    if (password && !password.value) {
        password.classList.add('error');
        if (passwordError) passwordError.style.display = 'block';
        isValid = false;
    }

    return isValid;
}

function validateRegisterForm() {
    let isValid = true;
    const name = document.getElementById('register-name');
    const email = document.getElementById('register-email');
    const password = document.getElementById('register-password');
    const confirmPassword = document.getElementById('register-confirm-password');
    
    const nameError = document.getElementById('register-name-error');
    const emailError = document.getElementById('register-email-error');
    const passwordError = document.getElementById('register-password-error');
    const confirmPasswordError = document.getElementById('register-confirm-password-error');

    // Reset errors
    if (name) name.classList.remove('error');
    if (email) email.classList.remove('error');
    if (password) password.classList.remove('error');
    if (confirmPassword) confirmPassword.classList.remove('error');
    
    if (nameError) nameError.style.display = 'none';
    if (emailError) emailError.style.display = 'none';
    if (passwordError) passwordError.style.display = 'none';
    if (confirmPasswordError) confirmPasswordError.style.display = 'none';

    // Validate name
    if (name && !name.value.trim()) {
        name.classList.add('error');
        if (nameError) nameError.style.display = 'block';
        isValid = false;
    }

    // Validate email
    if (email && (!email.value || !isValidEmail(email.value))) {
        email.classList.add('error');
        if (emailError) emailError.style.display = 'block';
        isValid = false;
    }

    // Validate password
    if (password && (!password.value || password.value.length < 8)) {
        password.classList.add('error');
        if (passwordError) passwordError.style.display = 'block';
        isValid = false;
    }

    // Validate confirm password
    if (password && confirmPassword && password.value !== confirmPassword.value) {
        confirmPassword.classList.add('error');
        if (confirmPasswordError) confirmPasswordError.style.display = 'block';
        isValid = false;
    }

    return isValid;
}

function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Video generation function
function generateVideo() {
    const button = this;
    const originalText = button.innerHTML;
    const uploadArea = document.querySelector('.upload-area');
    const musicStyle = document.querySelector('.music-option.active').textContent;
    
    // Check if files are selected
    if (!uploadArea.files || uploadArea.files.length === 0) {
        alert('Please select at least one photo to generate a video');
        return;
    }
    
    // Show loading state
    button.innerHTML = '<span class="spinner"></span> Generating...';
    button.disabled = true;
    
    // Create FormData for file upload
    const formData = new FormData();
    for (let i = 0; i < uploadArea.files.length; i++) {
        formData.append('photos', uploadArea.files[i]);
    }
    formData.append('music_style', musicStyle);
    
    // Send request to server
    fetch('/generate_video', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            alert('Video generated successfully! Download link: ' + data.video_url);
            
            // Reset form
            if (uploadArea) {
                uploadArea.innerHTML = `
                    <i class="fas fa-cloud-upload-alt"></i>
                    <h3>Click to Upload Photos</h3>
                    <p>Select 5-10 photos for best results</p>
                `;
                uploadArea.files = null;
            }
        } else {
            alert('Error generating video: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while generating the video');
    })
    .finally(() => {
        // Reset button
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

// Admin panel functionality
function showAdminPanel() {
    document.getElementById('auth-container').style.display = 'none';
    document.getElementById('admin-panel').style.display = 'block';
}

function logout() {
    fetch('/logout')
    .then(() => {
        window.location.href = '/';
    })
    .catch(error => {
        console.error('Error:', error);
        window.location.href = '/';
    });
}



