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

    let citationMatched = false;

    if (citations && citations.length > 0) {
        citations.forEach(cite => {
            const escapedId = cite.id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            // Strict [ID: ...] format replacement
            const inlineRegex = new RegExp(`\\[ID: ${escapedId}\\]`, 'g');
            
            const btnLabel = (cite.section && cite.section !== 'N/A' && cite.section.length < 30)
                ? `${cite.section}` 
                : `Page ${cite.page}`;
            
            const btnHtml = `<button onclick="viewProof('${cite.url}', ${cite.page || 1})" 
                         class="btn btn-sm btn-outline-primary py-0 px-1 mx-1 fw-bold text-decoration-none citation-inline-btn"
                         title="Verify Evidence: ${cite.title}">
                    <i class="bi bi-file-earmark-check me-1"></i>${btnLabel}
                </button>`;

            if (inlineRegex.test(processedText)) {
                processedText = processedText.replace(inlineRegex, btnHtml);
                citationMatched = true;
            }
        });

        // FALLBACK: If no inline citations were successfully matched, add them at the bottom
        if (sender === 'bot' && !citationMatched) {
            let sourcesHtml = '<div class="mt-3 border-top pt-2"><small class="text-muted d-block mb-1">Source References:</small><div class="d-flex flex-wrap gap-1">';
            citations.forEach(cite => {
                const btnLabel = (cite.section && cite.section !== 'N/A' && cite.section.length < 30)
                    ? `${cite.section}` 
                    : `Page ${cite.page}`;
                sourcesHtml += `<button onclick="viewProof('${cite.url}', ${cite.page || 1})" 
                         class="btn btn-sm btn-outline-secondary py-0 px-1 fw-normal citation-fallback-btn">
                    <i class="bi bi-link-45deg"></i> ${cite.title} (${btnLabel})
                </button>`;
            });
            sourcesHtml += '</div></div>';
            processedText += sourcesHtml;
        }
    }

    // Clean up extra spaces or artifacts
    processedText = processedText.replace(/\s{2,}/g, ' ');

    msgDiv.innerHTML = `
        <div class="message-content">${processedText}</div>
        ${sender === 'bot' ? '<div class="message-meta">Verified Legal Data • Non-Advice</div>' : ''}
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
