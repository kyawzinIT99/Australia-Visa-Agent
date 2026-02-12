// Chat functionality
console.log('AI Visa Assistant: initializing...');

try {
    const chatToggle = document.createElement('button');
    chatToggle.id = 'chat-toggle';
    chatToggle.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
    `;
    chatToggle.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #557aff, #00f2fe);
        border: none;
        cursor: pointer;
        box-shadow: 0 8px 24px rgba(85, 122, 255, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        z-index: 9999;
    `;
    chatToggle.onmouseover = () => {
        chatToggle.style.transform = 'scale(1.1)';
        chatToggle.style.boxShadow = '0 12px 32px rgba(85, 122, 255, 0.6)';
    };
    chatToggle.onmouseout = () => {
        chatToggle.style.transform = 'scale(1)';
        chatToggle.style.boxShadow = '0 8px 24px rgba(85, 122, 255, 0.4)';
    };

    // Create chat panel
    const chatPanel = document.createElement('div');
    chatPanel.id = 'chat-panel';
    chatPanel.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 400px;
        height: 600px;
        background: rgba(17, 24, 39, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        display: none;
        flex-direction: column;
        z-index: 10000;
        transition: all 0.3s ease;
    `;

    chatPanel.innerHTML = `
        <div style="padding: 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #f8fafc;">🧠 AI Visa Assistant</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Powered by real-time search</div>
            </div>
            <button id="chat-close" style="background: none; border: none; color: #94a3b8; font-size: 24px; cursor: pointer; padding: 0; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">✕</button>
        </div>
        <div id="chat-messages" style="flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px;">
            <div style="display: flex; flex-direction: column; align-items: flex-start;">
                <div style="max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); color: #f8fafc;">
                    <strong>👋 Hello!</strong> I'm your Australia Visa Assistant. I can help you with:<br>
                    • Understanding visa requirements<br>
                    • Completing documents<br>
                    • Answering visa questions<br><br>
                    Ask me anything about Australian visas!
                </div>
            </div>
        </div>
        <div style="padding: 20px; border-top: 1px solid rgba(255, 255, 255, 0.08); display: flex; gap: 12px;">
            <input type="text" id="chat-input" placeholder="Ask about visa requirements..." style="flex: 1; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px 16px; color: #f8fafc; font-size: 14px; outline: none;" />
            <button id="chat-send" style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #557aff, #00f2fe); border: none; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            </button>
        </div>
    `;

    document.body.appendChild(chatToggle);
    document.body.appendChild(chatPanel);

    // Chat toggle functionality
    chatToggle.addEventListener('click', () => {
        console.log('AI Visa Assistant: Opening chat panel');
        chatPanel.style.display = 'flex';
        chatToggle.style.display = 'none';
        setTimeout(() => document.getElementById('chat-input').focus(), 100);
    });

    document.getElementById('chat-close').addEventListener('click', () => {
        console.log('AI Visa Assistant: Closing chat panel');
        chatPanel.style.display = 'none';
        chatToggle.style.display = 'flex';
    });

    // Chat send functionality
    async function sendMessage() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('chat-send');
        const message = input.value.trim();

        if (!message) return;

        console.log('AI Visa Assistant: Sending message:', message);

        const messagesContainer = document.getElementById('chat-messages');

        // Disable input while sending
        input.disabled = true;
        sendBtn.disabled = true;
        sendBtn.style.opacity = '0.7';

        // Add user message
        const userMsg = document.createElement('div');
        userMsg.style.cssText = 'display: flex; flex-direction: column; align-items: flex-end;';
        userMsg.innerHTML = `<div style="max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; background: linear-gradient(135deg, #557aff, #00f2fe); color: white;">${message.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>`;
        messagesContainer.appendChild(userMsg);

        input.value = '';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Show typing indicator
        const typingMsg = document.createElement('div');
        typingMsg.id = 'typing-indicator';
        typingMsg.style.cssText = 'display: flex; flex-direction: column; align-items: flex-start;';
        typingMsg.innerHTML = `<div style="padding: 12px 16px; border-radius: 16px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08);"><div style="display: flex; gap: 4px;"><div style="width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; animation: typing 1.4s infinite;"></div><div style="width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; animation: typing 1.4s 0.2s infinite;"></div><div style="width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; animation: typing 1.4s 0.4s infinite;"></div></div></div>`;
        messagesContainer.appendChild(typingMsg);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            console.log('AI Visa Assistant: Fetching response...');
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });

            console.log('AI Visa Assistant: Response status:', response.status);

            const data = await response.json();

            // Remove typing indicator
            if (document.getElementById('typing-indicator')) {
                document.getElementById('typing-indicator').remove();
            }

            if (data.error) {
                console.error('AI Visa Assistant: API Error:', data.error);
                const errorMsg = document.createElement('div');
                errorMsg.style.cssText = 'display: flex; flex-direction: column; align-items: flex-start;';
                errorMsg.innerHTML = `<div style="max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; background: rgba(255, 77, 77, 0.15); border: 1px solid rgba(255, 77, 77, 0.3); color: #ff4d4d;">${data.error}</div>`;
                messagesContainer.appendChild(errorMsg);
            } else {
                console.log('AI Visa Assistant: Received response');
                const assistantMsg = document.createElement('div');
                assistantMsg.style.cssText = 'display: flex; flex-direction: column; align-items: flex-start;';

                // Format sources with proper styling
                let sourcesHtml = '';
                if (data.sources && data.sources.length > 0) {
                    sourcesHtml = '<div style="font-size: 11px; color: #94a3b8; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);"><strong>Sources:</strong><br>' +
                        data.sources.map(s => `<a href="${s.url}" target="_blank" style="color: #00f2fe; text-decoration: none; display: block; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">• ${s.title}</a>`).join('') +
                        '</div>';
                }

                // Process response - newlines to <br> and bold text
                let formattedResponse = data.response
                    .replace(/\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

                assistantMsg.innerHTML = `<div style="max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); color: #f8fafc;">${formattedResponse}${sourcesHtml}</div>`;
                messagesContainer.appendChild(assistantMsg);
            }

            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } catch (error) {
            console.error('AI Visa Assistant: Network/Script Error:', error);

            // Remove typing indicator if it exists
            if (document.getElementById('typing-indicator')) {
                document.getElementById('typing-indicator').remove();
            }

            const errorMsg = document.createElement('div');
            errorMsg.style.cssText = 'display: flex; flex-direction: column; align-items: flex-start;';
            errorMsg.innerHTML = `<div style="max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; background: rgba(255, 77, 77, 0.15); border: 1px solid rgba(255, 77, 77, 0.3); color: #ff4d4d;">Sorry, I encountered an error connecting to the server. Please check your internet connection and try again.</div>`;
            messagesContainer.appendChild(errorMsg);
        } finally {
            // Re-enable input
            input.disabled = false;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
            input.focus();
        }
    }

    document.getElementById('chat-send').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Add typing animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes typing {
            0%, 60%, 100% { opacity: 0.3; }
            30% { opacity: 1; }
        }
    `;
    document.head.appendChild(style);

    console.log('AI Visa Assistant: loaded successfully');

} catch (e) {
    console.error('AI Visa Assistant: Startup Error:', e);
}

