document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Auto-resize textarea as user types
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Handle send button click
    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            // Add user message to chat
            addMessage(message, 'user');
            
            // Clear input
            userInput.value = '';
            userInput.style.height = 'auto';
            
            // Show loading message
            const loadingId = addMessage('Thinking...', 'assistant');
            
            // Send request to server
            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            })
            .then(response => response.json())
            .then(data => {
                // Replace loading message with response
                replaceMessage(loadingId, data.response, 'assistant');
            })
            .catch(error => {
                console.error('Error:', error);
                replaceMessage(loadingId, 'Sorry, there was an error processing your request.', 'assistant');
            });
        }
    }

    // Add message to chat
    function addMessage(text, sender) {
        const messageId = Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.id = `message-${messageId}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${formatMessage(text)}
            </div>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return messageId;
    }

    // Replace message content
    function replaceMessage(messageId, text, sender) {
        const messageDiv = document.getElementById(`message-${messageId}`);
        if (messageDiv) {
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${formatMessage(text)}
                </div>
            `;
        }
    }

    // Format message with markdown-like syntax
    function formatMessage(text) {
        // Convert code blocks
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // Convert line breaks to <br>
        text = text.replace(/\n/g, '<br>');
        return text;
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
