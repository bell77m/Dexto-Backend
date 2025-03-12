document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const createSessionBtn = document.getElementById('create-session-btn');
    const joinSessionBtn = document.getElementById('join-session-btn');
    const leaveSessionBtn = document.getElementById('leave-session-btn');
    const sessionIdInput = document.getElementById('session-id-input');
    const currentSessionIdEl = document.getElementById('current-session-id');
    const sessionInfoEl = document.getElementById('session-info');
    const codeEditor = document.getElementById('code-editor');
    const statusIndicator = document.getElementById('status');
    const copySessionIdBtn = document.getElementById('copy-session-id');
    const notificationEl = document.getElementById('notification');
    const participantCountEl = document.getElementById('participant-count');
    
    // State
    let socket = null;
    let currentSessionId = null;
    let isConnected = false;
    let lastCursorPosition = 0;
    let ignoreNextUpdate = false;
    let participantCount = 1;
    
    // Function to show notification
    function showNotification(message, color = '#28a745') {
        notificationEl.textContent = message;
        notificationEl.style.backgroundColor = color;
        notificationEl.style.opacity = 1;
        
        setTimeout(() => {
            notificationEl.style.opacity = 0;
        }, 3000);
    }
    
    // Function to update connection status
    function updateConnectionStatus(connected) {
        isConnected = connected;
        
        if (connected) {
            statusIndicator.textContent = 'Connected';
            statusIndicator.classList.remove('disconnected');
            statusIndicator.classList.add('connected');
            codeEditor.disabled = false;
            leaveSessionBtn.disabled = false;
            createSessionBtn.disabled = true;
            joinSessionBtn.disabled = true;
            sessionIdInput.disabled = true;
            sessionInfoEl.style.display = 'block';
        } else {
            statusIndicator.textContent = 'Disconnected';
            statusIndicator.classList.remove('connected');
            statusIndicator.classList.add('disconnected');
            codeEditor.disabled = true;
            leaveSessionBtn.disabled = true;
            createSessionBtn.disabled = false;
            joinSessionBtn.disabled = false;
            sessionIdInput.disabled = false;
            sessionInfoEl.style.display = 'none';
            codeEditor.value = '';
            participantCount = 1;
            updateParticipantCount();
        }
    }
    
    // Function to update participant count display
    function updateParticipantCount() {
        participantCountEl.textContent = `Participants: ${participantCount}`;
    }
    
    // Function to connect to WebSocket
    async function connectWebSocket(sessionId) {
        // Close existing socket if any
        if (socket) {
            socket.close();
        }
        
        // Determine WebSocket protocol based on page protocol
        let serverIP = (await (await fetch("/server-ip")).json())?.ip;
        const wsUrl = `wss://${serverIP}/ws/session/${sessionId}`;
        
        socket = new WebSocket(wsUrl);
        
        socket.onopen = () => {
            currentSessionId = sessionId;
            currentSessionIdEl.textContent = sessionId;
            updateConnectionStatus(true);
            showNotification('Connected to session');
        };
        
        socket.onclose = () => {
            if (isConnected) {
                showNotification('Disconnected from session', '#dc3545');
            }
            updateConnectionStatus(false);
            currentSessionId = null;
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            showNotification('Connection error', '#dc3545');
        };
        
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'code_update') {
                ignoreNextUpdate = true;
                
                // Save cursor position
                lastCursorPosition = codeEditor.selectionStart;
                
                // Update code
                codeEditor.value = data.content;
                
                // Restore cursor position if possible
                if (lastCursorPosition <= codeEditor.value.length) {
                    codeEditor.setSelectionRange(lastCursorPosition, lastCursorPosition);
                }
            } else if (data.type === 'participant_update') {
                participantCount = data.count;
                updateParticipantCount();
            }
        };
    }
    
    // Create a new session
    createSessionBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/session-id');
            const data = await response.json();
            const sessionId = data.session_id;
            
            connectWebSocket(sessionId);
        } catch (error) {
            console.error('Error creating session:', error);
            showNotification('Error creating session', '#dc3545');
        }
    });
    
    // Join an existing session
    joinSessionBtn.addEventListener('click', () => {
        const sessionId = sessionIdInput.value.trim();
        
        if (!sessionId) {
            showNotification('Please enter a session ID', '#ffc107');
            return;
        }
        
        connectWebSocket(sessionId);
    });
    
    // Leave the current session
    leaveSessionBtn.addEventListener('click', () => {
        if (socket) {
            socket.close();
        }
    });
    
    // Handle code changes and send updates
    let debounceTimeout;
    codeEditor.addEventListener('input', () => {
        if (ignoreNextUpdate) {
            ignoreNextUpdate = false;
            return;
        }
        
        // Save cursor position
        lastCursorPosition = codeEditor.selectionStart;
        
        // Debounce to reduce network traffic
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                const data = {
                    type: 'code_update',
                    content: codeEditor.value
                };
                socket.send(JSON.stringify(data));
            }
        }, 100);
    });
    
    // Copy session ID to clipboard
    copySessionIdBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(currentSessionId).then(() => {
            showNotification('Session ID copied to clipboard');
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    });
    
    // Handle session ID input on pressing Enter
    sessionIdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            joinSessionBtn.click();
        }
    });
    
    // Initial state
    updateConnectionStatus(false);
});