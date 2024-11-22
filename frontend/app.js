// AWS Configuration
const API_ENDPOINT = '/api';
let currentUser = null;

// DOM Elements
const authNav = document.getElementById('auth-nav');
const userInfo = document.getElementById('user-info');
const authButtons = document.getElementById('auth-buttons');
const authForms = document.getElementById('auth-forms');
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const appointmentForm = document.getElementById('appointment-form');
const appointmentsList = document.getElementById('appointments-list');
const userEmailSpan = document.getElementById('user-email');

// Auth Form Handlers
document.getElementById('login-btn').addEventListener('click', () => {
    authForms.style.display = 'block';
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('signup-section').style.display = 'none';
});

document.getElementById('signup-btn').addEventListener('click', () => {
    authForms.style.display = 'block';
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('signup-section').style.display = 'block';
});

document.getElementById('logout-btn').addEventListener('click', async () => {
    try {
        await fetch(`${API_ENDPOINT}/auth/logout`, { method: 'POST' });
        currentUser = null;
        updateAuthUI();
    } catch (error) {
        showError('Logout failed. Please try again.');
    }
});

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(loginForm);
    
    try {
        const response = await fetch(`${API_ENDPOINT}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: formData.get('email'),
                password: formData.get('password')
            })
        });

        if (!response.ok) throw new Error('Login failed');
        
        const data = await response.json();
        currentUser = data.user;
        updateAuthUI();
        loadUserAppointments();
    } catch (error) {
        showError('Login failed. Please check your credentials.');
    }
});

signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(signupForm);
    
    if (formData.get('password') !== formData.get('confirm-password')) {
        showError('Passwords do not match');
        return;
    }

    try {
        const response = await fetch(`${API_ENDPOINT}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: formData.get('email'),
                password: formData.get('password')
            })
        });

        if (!response.ok) throw new Error('Signup failed');
        
        showSuccess('Account created! Please check your email for verification.');
        document.getElementById('login-btn').click();
    } catch (error) {
        showError('Signup failed. Please try again.');
    }
});

// Appointment Form Handler
appointmentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentUser) {
        showError('Please login to book an appointment');
        return;
    }

    const formData = new FormData(appointmentForm);
    const appointmentData = {
        carMake: formData.get('car-make'),
        carModel: formData.get('car-model'),
        carYear: formData.get('car-year'),
        serviceType: formData.get('service-type'),
        date: formData.get('date'),
        time: formData.get('time'),
        description: formData.get('description'),
        notificationPreference: formData.get('notification-preference') === 'on'
    };

    try {
        // Handle image upload if present
        const imageFile = formData.get('car-image');
        if (imageFile && imageFile.size > 0) {
            const imageUrl = await uploadImage(imageFile);
            appointmentData.imageUrl = imageUrl;
        }

        const response = await fetch(`${API_ENDPOINT}/appointments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(appointmentData)
        });

        if (!response.ok) throw new Error('Failed to book appointment');

        showSuccess('Appointment booked successfully!');
        appointmentForm.reset();
        loadUserAppointments();
    } catch (error) {
        showError('Failed to book appointment. Please try again.');
    }
});

// Image Upload Handler
async function uploadImage(file) {
    try {
        // Get presigned URL
        const response = await fetch(`${API_ENDPOINT}/upload-url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileName: file.name, fileType: file.type })
        });

        if (!response.ok) throw new Error('Failed to get upload URL');
        
        const { uploadUrl, imageUrl } = await response.json();

        // Upload to S3
        await fetch(uploadUrl, {
            method: 'PUT',
            body: file,
            headers: { 'Content-Type': file.type }
        });

        return imageUrl;
    } catch (error) {
        throw new Error('Image upload failed');
    }
}

// Load User Appointments
async function loadUserAppointments() {
    if (!currentUser) return;

    try {
        const response = await fetch(`${API_ENDPOINT}/appointments`);
        if (!response.ok) throw new Error('Failed to load appointments');

        const appointments = await response.json();
        displayAppointments(appointments);
    } catch (error) {
        showError('Failed to load appointments');
    }
}

// Display Appointments
function displayAppointments(appointments) {
    const container = document.getElementById('appointments-container');
    container.innerHTML = '';

    appointments.forEach(appointment => {
        const card = document.createElement('div');
        card.className = 'appointment-card fade-in';
        card.innerHTML = `
            <h3>${appointment.serviceType}</h3>
            <p><strong>Vehicle:</strong> ${appointment.carYear} ${appointment.carMake} ${appointment.carModel}</p>
            <p><strong>Date:</strong> ${formatDate(appointment.date)}</p>
            <p><strong>Time:</strong> ${appointment.time}</p>
            <p><strong>Status:</strong> <span class="status-${appointment.status.toLowerCase()}">${appointment.status}</span></p>
            ${appointment.imageUrl ? `<img src="${appointment.imageUrl}" alt="Car Image" style="max-width: 100%; margin-top: 1rem;">` : ''}
        `;
        container.appendChild(card);
    });

    appointmentsList.style.display = appointments.length ? 'block' : 'none';
}

// UI Helpers
function updateAuthUI() {
    if (currentUser) {
        userInfo.style.display = 'block';
        authButtons.style.display = 'none';
        authForms.style.display = 'none';
        userEmailSpan.textContent = currentUser.email;
        appointmentsList.style.display = 'block';
    } else {
        userInfo.style.display = 'none';
        authButtons.style.display = 'block';
        appointmentsList.style.display = 'none';
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error fade-in';
    errorDiv.textContent = message;
    document.querySelector('main').insertBefore(errorDiv, document.querySelector('main').firstChild);
    setTimeout(() => errorDiv.remove(), 5000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success fade-in';
    successDiv.textContent = message;
    document.querySelector('main').insertBefore(successDiv, document.querySelector('main').firstChild);
    setTimeout(() => successDiv.remove(), 5000);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Initialize
updateAuthUI();
