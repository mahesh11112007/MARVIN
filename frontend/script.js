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
    
    // Show interactive modal instead of alert
    showActionModal(action);
}

// Create and show custom modal
function showActionModal(action) {
    // Remove existing modal if any
    const existingModal = document.querySelector('.action-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'action-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>🤖 ${action.toUpperCase()}</h2>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p>This is a <strong>demo interface</strong> for the ${action} endpoint.</p>
                <p>To use this feature, send a POST request to:</p>
                <code>POST /api/${action.toLowerCase()}</code>
                <div class="endpoint-info">
                    <h3>Available Endpoints:</h3>
                    <ul>
                        <li><span class="endpoint">POST /create</span> - Create new files</li>
                        <li><span class="endpoint">POST /upload</span> - Upload files for processing</li>
                        <li><span class="endpoint">POST /analyze</span> - Analyze code structure</li>
                        <li><span class="endpoint">POST /optimize</span> - Optimize and improve code</li>
                    </ul>
                </div>
            </div>
            <div class="modal-footer">
                <button class="demo-btn" onclick="simulateAction('${action}')">Try Demo</button>
                <button class="close-modal-btn" onclick="closeModal()">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Animate modal in
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
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

// Simulate action for demo
function simulateAction(action) {
    const modalBody = document.querySelector('.modal-body');
    modalBody.innerHTML = `
        <div class="loading-spinner"></div>
        <p>Processing ${action} request...</p>
    `;
    
    setTimeout(() => {
        modalBody.innerHTML = `
            <div class="success-message">✅ Demo Complete!</div>
            <p>In production, this would ${getActionDescription(action)}.</p>
            <p>Connect your backend to enable full functionality.</p>
        `;
    }, 2000);
}

// Get action description
function getActionDescription(action) {
    const descriptions = {
        'Create File': 'create a new file with AI assistance',
        'Upload File': 'upload and process your code files',
        'Analyze Code': 'analyze your code for bugs and improvements',
        'Optimize Code': 'optimize your code for better performance'
    };
    return descriptions[action] || 'perform the requested action';
}

// Add hover sound effect (optional, subtle)
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
    
    if (shortcuts[e.key]) {
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
