// Utility functions
function showError(message, elementId = 'error') {
    const errorDiv = document.getElementById(elementId);
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

function showSuccess(message, elementId = 'success') {
    const successDiv = document.getElementById(elementId);
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }
}

function hideMessages() {
    const errorDiv = document.getElementById('error');
    const successDiv = document.getElementById('success');
    if (errorDiv) errorDiv.style.display = 'none';
    if (successDiv) successDiv.style.display = 'none';
}

// Sign up functionality
async function handleSignUp(event) {
    event.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        
        if (data.success) {
            showSuccess("Signup successful! Redirecting to sign in...");
            setTimeout(() => {
                window.location.href = "/signin";
            }, 2000);
        } else {
            showError("Signup failed: " + data.message);
        }
    } catch (error) {
        showError("Network error. Please try again.");
    }
}

// Sign in functionality
async function handleSignIn(event) {
    event.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    try {
        const response = await fetch('/signin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        
        if (data.success) {
            showSuccess("Login successful! Redirecting...");
            setTimeout(() => {
                window.location.href = "/chat";
            }, 1500);
        } else {
            showError("Login failed: " + data.message);
        }
    } catch (error) {
        showError("Network error. Please try again.");
    }
}

// Chat functionality
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    messageInput.value = '';
    
    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing';
    typingDiv.innerHTML = 'Therabot is typing...';
    typingDiv.id = 'typing-indicator';
    document.getElementById('chatMessages').appendChild(typingDiv);
    scrollToBottom();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        if (data.success) {
            // Add bot response after a slight delay for realism
            setTimeout(() => {
                addMessage(data.response, 'bot');
            }, 500);
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        // Remove typing indicator
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        addMessage('Sorry, I encountered a network error. Please try again.', 'bot');
    }
}

function addMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'bot-message'}`;
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add welcome message if on chat page
    if (document.getElementById('chatMessages')) {
        setTimeout(() => {
            addMessage("Hello there! I'm Therabot, and I'm really glad you decided to reach out today. This space is entirely yours - you can share whatever is on your mind or in your heart. I'm here to listen without judgment and support you however I can. How are you feeling in this moment?", 'bot');
        }, 500);
    }
    
    // Focus on message input if on chat page
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        setTimeout(() => {
            messageInput.focus();
        }, 1000);
    }
});