const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    userInput.value = '';
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    
    try {
        const response = await fetch('/api/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        // Add bot response
        addMessage(data.response, 'bot');
        
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    }
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex items-start space-x-3 animate-slide-up`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-user text-blue-500 text-sm"></i>
            </div>
            <div class="flex-1 bg-blue-600/20 rounded-lg p-3 max-w-[80%]">
                <p class="text-white text-sm">${escapeHtml(text)}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="w-8 h-8 bg-pink-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-robot text-pink-500 text-sm"></i>
            </div>
            <div class="flex-1 bg-gray-900/50 rounded-lg p-3 max-w-[80%]">
                <p class="text-gray-300 text-sm whitespace-pre-line">${escapeHtml(text)}</p>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'flex items-start space-x-3';
    typingDiv.innerHTML = `
        <div class="w-8 h-8 bg-pink-500/20 rounded-full flex items-center justify-center flex-shrink-0">
            <i class="fas fa-robot text-pink-500 text-sm"></i>
        </div>
        <div class="flex-1 bg-gray-900/50 rounded-lg p-3 max-w-[80%]">
            <div class="flex space-x-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) element.remove();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}