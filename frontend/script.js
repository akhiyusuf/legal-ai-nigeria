console.log("Legal AI: script.js v2.0 (Modern Layout) loaded");

document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});

document.querySelector('.new-chat-btn').addEventListener('click', () => {
    document.getElementById('chat-box').innerHTML = `
        <div class="message bot-message">
            <div class="message-content">Hello! How can I help you today?</div>
        </div>`;
    chatHistory = [];
    document.getElementById('active-sources-list').innerHTML = '';
});

let chatHistory = [];
let activeSources = new Set();

async function sendMessage() {
    const input = document.getElementById('user-input');
    const query = input.value.trim();
    
    if (!query) return;

    // Display user message
    appendMessage('user', query);
    input.value = '';

    // Show loading
    const loadingDiv = appendMessage('bot', 'Processing query...');

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                query: query, 
                history: chatHistory,
                top_k: 5 
            })
        });
        
        const data = await response.json();
        
        // Remove loading
        loadingDiv.remove();

        // Display Answer
        appendMessage('bot', data.answer, data.citations);

        // Update history
        chatHistory.push({ role: 'user', content: query });
        chatHistory.push({ role: 'assistant', content: data.answer });

        // Keep history manageable
        if (chatHistory.length > 10) chatHistory = chatHistory.slice(-10);

        // Update Sidebar Sources
        updateSidebarSources(data.citations);

    } catch (error) {
        loadingDiv.textContent = 'Error connecting to the legal system. Please try again later.';
        console.error(error);
    }
}

function appendMessage(sender, text, citations = []) {
    const chatBox = document.getElementById('chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-message`;
    
    let processedText = text.split('\n').join('<br>');

    // SAFETY: Clean up any accidentally leaked metadata tags (like [[ DOCUMENT: ... ]])
    processedText = processedText.replace(/\[\[ DOCUMENT:.*?\| LOCATION:.*? \]\]/g, '');

    if (citations && citations.length > 0) {
        citations.forEach(cite => {
            const escapedId = cite.id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regexPatterns = [
                new RegExp(`\\[ID: ${escapedId}\\]`, 'g'),
                new RegExp(`\\[${escapedId}\\]`, 'g'),
                new RegExp(`\\(${escapedId}\\)`, 'g'),
                new RegExp(`${escapedId}`, 'g') // Handle raw IDs
            ];
            
            const btnLabel = cite.section && cite.section !== 'N/A' 
                ? `[Proof: ${cite.section}]` 
                : `[Proof: Page ${cite.page}]`;
            
            const btnHtml = `<button onclick="viewProof('${cite.url}', ${cite.page || 1})" 
                         class="btn btn-sm btn-link p-0 fw-bold text-decoration-none citation-inline-btn">
                    ${btnLabel}
                </button>`;

            regexPatterns.forEach(pattern => {
                processedText = processedText.replace(pattern, btnHtml);
            });
        });
    }

    // Clean up extra spaces or artifacts from replacements
    processedText = processedText.replace(/\s{2,}/g, ' ').replace(/\( \)/g, '').replace(/\[ \]/g, '');

    msgDiv.innerHTML = `
        <div class="message-content">${processedText}</div>
        ${sender === 'bot' ? '<div class="message-meta">Source: Verified Official Law</div>' : ''}
    `;
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msgDiv;
}

function updateSidebarSources(citations) {
    const sidebarList = document.getElementById('active-sources-list');
    
    citations.forEach(cite => {
        const sourceId = cite.title || 'Legal Document';
        if (!activeSources.has(sourceId)) {
            activeSources.add(sourceId);
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';
            sourceItem.innerHTML = `<i class="bi bi-file-earmark-text me-2"></i>${sourceId}`;
            sourceItem.onclick = () => window.open(cite.url, '_blank');
            sidebarList.appendChild(sourceItem);
        }
    });
}

async function viewProof(url, page) {
    const modal = new bootstrap.Modal(document.getElementById('proofModal'));
    const img = document.getElementById('proof-img');
    img.src = ''; 
    modal.show();

    try {
        const proofUrl = `/proof?doc_url=${encodeURIComponent(url)}&page=${page}`;
        img.src = proofUrl;
    } catch (error) {
        alert('Could not load screenshot.');
    }
}
