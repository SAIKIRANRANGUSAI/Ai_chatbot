// static/js/chatbot.js
document.addEventListener('DOMContentLoaded', () => {
    const chatIcon = document.getElementById('chat-icon');
    const chatContainer = document.getElementById('chat-container');
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');

    chatIcon.addEventListener("click", () => {
  chatContainer.style.display = "flex";
  if (chatMessages.innerHTML.trim() === "") {
    appendMessage("bot", "Hi! 👋 I'm your assistant from The Colour Moon. How can I help you today? (e.g., website, app, SEO, support)");
  }
});


    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    function appendMessage(sender, text) {
        const msg = document.createElement('div');
        msg.classList.add('message', sender);
        msg.textContent = text;
        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        appendMessage('user', text);
        userInput.value = '';

        appendMessage('bot', '⏳ typing...');

        fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message: text })
        })
        .then(res => res.json())
        .then(data => {
            document.querySelectorAll('.bot').forEach(e => {
                if (e.textContent === '⏳ typing...') e.remove();
            });
            appendMessage('bot', data.reply || '⚠️ No response from server');
        })
        .catch(err => {
            console.error(err);
            appendMessage('bot', '⚠️ Error contacting server.');
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
