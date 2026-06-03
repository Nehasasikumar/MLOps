document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide Icons
    lucide.createIcons();

    // DOM Elements
    const statusBox = document.getElementById('statusBox');
    const statusText = document.getElementById('statusText');
    const quickTopics = document.getElementById('quickTopics');
    const messagesContainer = document.getElementById('messagesContainer');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const problemsContainer = document.getElementById('problemsContainer');

    const API_BASE_URL = 'http://127.0.0.1:5000/api';

    // 1. Check Backend Status
    async function checkStatus() {
        try {
            const res = await fetch(`${API_BASE_URL}/status`);
            if (!res.ok) throw new Error('Status endpoint returned error');
            const data = await res.json();
            
            const dot = statusBox.querySelector('.status-dot');
            if (data.status === 'ready') {
                dot.className = 'status-dot ready';
                statusText.textContent = `RAG Connected (${data.total_problems.toLocaleString()} Problems)`;
            } else {
                dot.className = 'status-dot loading';
                statusText.textContent = 'Building FAISS Index...';
                // Retry in 5 seconds if indexing
                setTimeout(checkStatus, 5000);
            }
        } catch (err) {
            console.error('Failed to connect to backend status API:', err);
            const dot = statusBox.querySelector('.status-dot');
            dot.className = 'status-dot error';
            statusText.textContent = 'Server Offline';
            // Retry in 5 seconds
            setTimeout(checkStatus, 5000);
        }
    }

    checkStatus();

    // 2. Setup Markdown Renderer
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    // 3. Chat Helpers
    function appendMessage(sender, content, isHtml = false, isSystem = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isSystem ? 'system' : sender} glass`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        let iconName = 'bot';
        if (sender === 'user') iconName = 'user';
        else if (isSystem) iconName = 'info';

        const iconEl = document.createElement('i');
        iconEl.setAttribute('data-lucide', iconName);
        avatarDiv.appendChild(iconEl);
        msgDiv.appendChild(avatarDiv);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isHtml) {
            contentDiv.innerHTML = content;
        } else {
            const p = document.createElement('p');
            p.textContent = content;
            contentDiv.appendChild(p);
        }
        
        msgDiv.appendChild(contentDiv);
        messagesContainer.appendChild(msgDiv);
        
        // Render Icons for dynamic components
        lucide.createIcons();
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return msgDiv;
    }

    function appendLoadingMessage() {
        const loadingHtml = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px; margin-bottom: 0;">Analyzing Leetcode FAISS vectors & generating answer...</p>
        `;
        return appendMessage('bot', loadingHtml, true);
    }

    // 4. Update Context Panel (Retrieved Problems)
    function renderRetrievedProblems(problems) {
        if (!problems || problems.length === 0) {
            problemsContainer.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="search-code" class="empty-icon"></i>
                    <p>No matching Leetcode problems retrieved for this query.</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        problemsContainer.innerHTML = '';
        
        problems.forEach(prob => {
            const card = document.createElement('a');
            card.className = 'problem-card';
            card.href = prob.link || `https://leetcode.com/problems/${prob.title.toLowerCase().replace(/ /g, '-')}/`;
            card.target = '_blank';

            // Calculate Upvote ratio
            const totalVotes = prob.likes + prob.dislikes;
            const likeRatio = totalVotes > 0 ? Math.round((prob.likes / totalVotes) * 100) : 100;
            
            // Format difficulty class
            const diffClass = prob.difficulty.toLowerCase();

            card.innerHTML = `
                <div class="card-header">
                    <span class="card-title">${prob.id}. ${prob.title}</span>
                    <span class="difficulty-badge ${diffClass}">${prob.difficulty}</span>
                </div>
                <div class="card-topics">
                    ${prob.topics.slice(0, 3).map(t => `<span class="card-topic-tag">${t}</span>`).join('')}
                    ${prob.topics.length > 3 ? `<span class="card-topic-tag">+${prob.topics.length - 3} more</span>` : ''}
                </div>
                <div class="card-stats">
                    <div class="stat-group">
                        <i data-lucide="percent"></i>
                        <span>Acc: ${prob.acceptance_rate}%</span>
                    </div>
                    <div class="stat-group" title="${prob.likes.toLocaleString()} Likes / ${prob.dislikes.toLocaleString()} Dislikes">
                        <div class="like-bar">
                            <div class="like-bar-fill" style="width: ${likeRatio}%"></div>
                        </div>
                        <span>${likeRatio}% likes</span>
                    </div>
                </div>
            `;
            
            problemsContainer.appendChild(card);
        });

        lucide.createIcons();
    }

    // 5. Handle Form Submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to UI
        appendMessage('user', message);
        messageInput.value = '';
        messageInput.rows = 1;

        // Add loading message
        const loadingMessageEl = appendLoadingMessage();

        // Lock form during submission
        messageInput.disabled = true;
        sendBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message
                })
            });

            const data = await response.json();
            
            // Remove loading indicator
            loadingMessageEl.remove();

            if (!response.ok) {
                appendMessage('bot', `<strong>Error:</strong> ${data.error || 'Failed to get a response.'}`, true);
                return;
            }

            // Render Markdown Bot Response
            const markdownHtml = marked.parse(data.answer);
            appendMessage('bot', markdownHtml, true);

            // Highlight Code Snippets using Prism
            Prism.highlightAll();

            // Render Retrieved Problems on the side panel
            renderRetrievedProblems(data.problems);

        } catch (err) {
            console.error('Error sending message:', err);
            loadingMessageEl.remove();
            appendMessage('bot', `<strong>Connection Error:</strong> Could not connect to the backend server. Please verify the Flask server is running at <code>${API_BASE_URL}</code>.`, true);
        } finally {
            // Unlock form
            messageInput.disabled = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    });

    // 6. Auto-expand input text area
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = `${Math.min(messageInput.scrollHeight, 120)}px`;
    });

    // 7. Handle Topic Badge Clicks
    quickTopics.addEventListener('click', (e) => {
        if (e.target.classList.contains('topic-badge')) {
            const topic = e.target.textContent;
            messageInput.value = `Explain the pattern for "${topic}" and list some key problems.`;
            messageInput.focus();
            // Trigger height resize
            messageInput.style.height = 'auto';
            messageInput.style.height = `${messageInput.scrollHeight}px`;
        }
    });

    // 8. Clear Chat
    clearChatBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear your chat history?')) {
            // Remove all except welcome message
            const messages = messagesContainer.querySelectorAll('.message:not(.system)');
            messages.forEach(m => m.remove());
            problemsContainer.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="search-code" class="empty-icon"></i>
                    <p>Submit a query to inspect the top-K problems retrieved from the FAISS database.</p>
                </div>
            `;
            lucide.createIcons();
        }
    });
});
