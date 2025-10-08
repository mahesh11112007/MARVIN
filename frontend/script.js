// Backend API base URL (change this to your actual backend URL)
const API_BASE_URL = window.location.origin.includes('github.io') 
    ? 'http://localhost:5000/api' 
    : '/api';

// Smooth scroll to top on page load
window.addEventListener('load', () => {
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease-in';
        document.body.style.opacity = '1';
    }, 100);
});

// Add ripple effect to buttons
function createRipple(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;
    ripple.style.width = ripple.style.height = `${diameter}px`;
    ripple.style.left = `${event.clientX - button.offsetLeft - radius}px`;
    ripple.style.top = `${event.clientY - button.offsetTop - radius}px`;
    ripple.classList.add('ripple');
    const rippleEffect = button.getElementsByClassName('ripple')[0];
    if (rippleEffect) {
        rippleEffect.remove();
    }
    button.appendChild(ripple);
}

// Enhanced button click handler with animations
function handleAction(action) {
    const button = event.target.closest('button');
    
    // Add click animation
    if (button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 150);
    }
    
    // Log action
    console.log(`Action clicked: ${action}`);
    
    // Show interactive modal with form
    showActionModal(action);
}

// Create and show custom modal with forms
function showActionModal(action) {
    // Remove existing modal if any
    const existingModal = document.querySelector('.action-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'action-modal';
    
    let formHTML = '';
    
    // Generate form based on action type
    switch(action) {
        case 'Create File':
            formHTML = `
                <form id="actionForm" onsubmit="submitAction(event, 'create')">
                    <div class="form-group">
                        <label for="filename">Filename:</label>
                        <input type="text" id="filename" name="filename" placeholder="e.g., main.py" required />
                    </div>
                    <div class="form-group">
                        <label for="code">Code:</label>
                        <textarea id="code" name="code" rows="10" placeholder="Enter your code here..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="language">Language (optional):</label>
                        <input type="text" id="language" name="language" placeholder="e.g., python, javascript" />
                    </div>
                    <button type="submit" class="submit-btn">Create File</button>
                </form>
            `;
            break;
            
        case 'Upload File':
            formHTML = `
                <form id="actionForm" onsubmit="submitAction(event, 'upload')">
                    <div class="form-group">
                        <label for="fileInput">Select File:</label>
                        <input type="file" id="fileInput" name="file" required />
                        <small>Upload a code file for processing</small>
                    </div>
                    <button type="submit" class="submit-btn">Upload File</button>
                </form>
            `;
            break;
            
        case 'Analyze Code':
            formHTML = `
                <form id="actionForm" onsubmit="submitAction(event, 'analyze')">
                    <div class="form-group">
                        <label for="filename">Filename (optional):</label>
                        <input type="text" id="filename" name="filename" placeholder="e.g., script.js" />
                    </div>
                    <div class="form-group">
                        <label for="code">Code to Analyze:</label>
                        <textarea id="code" name="code" rows="10" placeholder="Paste your code here..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="language">Language:</label>
                        <input type="text" id="language" name="language" placeholder="e.g., python, javascript" />
                    </div>
                    <button type="submit" class="submit-btn">Analyze Code</button>
                </form>
            `;
            break;
            
        case 'Optimize Code':
            formHTML = `
                <form id="actionForm" onsubmit="submitAction(event, 'optimize')">
                    <div class="form-group">
                        <label for="filename">Filename (optional):</label>
                        <input type="text" id="filename" name="filename" placeholder="e.g., app.py" />
                    </div>
                    <div class="form-group">
                        <label for="code">Code to Optimize:</label>
                        <textarea id="code" name="code" rows="10" placeholder="Paste your code here..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="language">Language:</label>
                        <input type="text" id="language" name="language" placeholder="e.g., python, javascript" />
                    </div>
                    <button type="submit" class="submit-btn">Optimize Code</button>
                </form>
            `;
            break;
    }
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                🤖 ${action.toUpperCase()}
                <button class="close-btn" onclick="closeModal()">×</button>
            </div>
            <div class="modal-body">
                ${formHTML}
            </div>
            <div id="responseArea" class="response-area" style="display:none;"></div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Animate modal in
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

// Submit action to backend
async function submitAction(event, endpoint) {
    event.preventDefault();
    
    const form = event.target;
    const responseArea = document.getElementById('responseArea');
    const modalBody = document.querySelector('.modal-body');
    
    // Show loading state
    responseArea.style.display = 'block';
    responseArea.innerHTML = '<div class="loading-spinner"></div><p>Processing request...</p>';
    
    try {
        let response;
        
        if (endpoint === 'upload') {
            // Handle file upload
            const formData = new FormData(form);
            response = await fetch(`${API_BASE_URL}/${endpoint}`, {
                method: 'POST',
                body: formData
            });
        } else {
            // Handle JSON data
            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });
            
            response = await fetch(`${API_BASE_URL}/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }
        
        const result = await response.json();
        
        if (response.ok) {
            // Success response
            displaySuccess(result, responseArea, modalBody);
        } else {
            // Error response
            displayError(result.error || 'Request failed', responseArea);
        }
    } catch (error) {
        console.error('Error:', error);
        displayError(`Connection error: ${error.message}. Make sure your backend is running at ${API_BASE_URL}`, responseArea);
    }
}

// Display success response
function displaySuccess(result, responseArea, modalBody) {
    modalBody.style.display = 'none';
    responseArea.innerHTML = `
        <div class="success-message">✅ Success!</div>
        <div class="response-content">
            <pre>${JSON.stringify(result, null, 2)}</pre>
        </div>
        <button onclick="resetModal()" class="reset-btn">Try Another Request</button>
        <button onclick="closeModal()" class="close-modal-btn">Close</button>
    `;
}

// Display error response
function displayError(errorMessage, responseArea) {
    responseArea.innerHTML = `
        <div class="error-message">❌ Error</div>
        <div class="error-content">
            <p>${errorMessage}</p>
        </div>
        <button onclick="resetModal()" class="reset-btn">Try Again</button>
        <button onclick="closeModal()" class="close-modal-btn">Close</button>
    `;
}

// Reset modal to show form again
function resetModal() {
    const modalBody = document.querySelector('.modal-body');
    const responseArea = document.getElementById('responseArea');
    
    modalBody.style.display = 'block';
    responseArea.style.display = 'none';
    responseArea.innerHTML = '';
    
    // Reset form
    const form = document.getElementById('actionForm');
    if (form) {
        form.reset();
    }
}

// Close modal function
function closeModal() {
    const modal = document.querySelector('.action-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

// Add hover effect
function addHoverEffect() {
    const buttons = document.querySelectorAll('button:not(.close-btn):not(.close-modal-btn)');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', () => {
            button.style.transition = 'all 0.3s ease';
        });
    });
}

// Parallax effect for hero section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const parallax = document.querySelector('.container');
    if (parallax) {
        parallax.style.transform = `translateY(${scrolled * 0.1}px)`;
    }
});

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    addHoverEffect();
    
    // Add ripple effect to all buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', createRipple);
    });
    
    // Add smooth reveal animation to elements
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });
    
    // Observe all major elements
    document.querySelectorAll('h1, .buttons, button').forEach(el => {
        el.classList.add('fade-in');
        observer.observe(el);
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape to close modal
    if (e.key === 'Escape') {
        closeModal();
    }
    
    // Number keys to trigger actions
    const shortcuts = {
        '1': 'Create File',
        '2': 'Upload File',
        '3': 'Analyze Code',
        '4': 'Optimize Code'
    };
    
    if (shortcuts[e.key] && !document.querySelector('.action-modal')) {
        e.preventDefault();
        handleAction(shortcuts[e.key]);
    }
});

// Add floating particles animation (optional eye candy)
function createParticle() {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = Math.random() * 100 + 'vw';
    particle.style.animationDuration = (Math.random() * 3 + 2) + 's';
    particle.style.opacity = Math.random() * 0.5 + 0.3;
    document.body.appendChild(particle);
    
    setTimeout(() => {
        particle.remove();
    }, 5000);
}

// Create particles periodically
setInterval(createParticle, 3000);
