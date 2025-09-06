let currentSessionId = null;
let isListening = false;
let lastAIMessage = '';

function startNewConversation() {
    currentSessionId = 'session_' + Date.now();
    document.getElementById('conversationArea').classList.add('active');
    document.getElementById('messages').innerHTML = '';
    
    // Start conversation
    fetch('/api/conversation/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: currentSessionId})
    })
    .then(response => response.json())
    .then(data => {
        addMessage(data.response, 'ai');
        lastAIMessage = data.response;
    });
}

function uploadResume() {
    const fileInput = document.getElementById('resumeFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/resume/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentSessionId = data.session_id;
            document.getElementById('conversationArea').classList.add('active');
            document.getElementById('messages').innerHTML = '';
            addMessage(data.message, 'ai');
            lastAIMessage = data.message;
        } else {
            alert('Error uploading resume: ' + data.message);
        }
    });
}

function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message || !currentSessionId) return;

    addMessage(message, 'user');
    input.value = '';

    fetch('/api/conversation/continue', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: currentSessionId,
            user_input: message
        })
    })
    .then(response => response.json())
    .then(data => {
        addMessage(data.response, 'ai');
        lastAIMessage = data.response;
        
        if (data.is_complete) {
            showResumeOptions(data.resume_data);
        }
    });
}

function addMessage(text, sender) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = text;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function toggleListening() {
    const btn = document.getElementById('listenBtn');
    
    if (isListening) {
        // Stop listening
        fetch('/api/voice/stop-listening', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: currentSessionId})
        });
        btn.classList.remove('active');
        isListening = false;
    } else {
        // Start listening
        fetch('/api/voice/start-listening', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: currentSessionId})
        });
        btn.classList.add('active');
        isListening = true;
    }
}

function speakLastMessage() {
    if (lastAIMessage) {
        fetch('/api/voice/speak', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: currentSessionId,
                text: lastAIMessage
            })
        });
    }
}

function showResumeOptions(resumeData) {
    const messagesDiv = document.getElementById('messages');
    const optionsDiv = document.createElement('div');
    optionsDiv.className = 'message ai-message';
    optionsDiv.innerHTML = `
        <h3>Resume Complete! 🎉</h3>
        <p>Your resume has been generated. Choose a format:</p>
        <button class="btn" onclick="downloadResume('html')">Download HTML</button>
        <button class="btn" onclick="downloadResume('pdf')">Download PDF</button>
        <button class="btn" onclick="downloadResume('text')">Download Text</button>
    `;
    messagesDiv.appendChild(optionsDiv);
}

function downloadResume(format) {
    if (!currentSessionId) return;

    fetch(`/api/resume/download/${format}?session_id=${currentSessionId}`)
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Download failed');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `resume.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        alert('Error downloading resume: ' + error.message);
    });
}
