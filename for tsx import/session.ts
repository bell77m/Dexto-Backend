export class SessionManager {
  // HTML Elements
  private createSessionBtn: HTMLButtonElement;
  private joinSessionBtn: HTMLButtonElement;
  private leaveSessionBtn: HTMLButtonElement;
  private sessionIdInput: HTMLInputElement;
  private currentSessionIdEl: HTMLElement;
  private sessionInfoEl: HTMLElement;
  private codeEditor: HTMLTextAreaElement;
  private statusIndicator: HTMLElement;
  private copySessionIdBtn: HTMLButtonElement;
  private notificationEl: HTMLElement;
  private participantCountEl: HTMLElement;

  // WebSocket and State
  private ws: WebSocket | null = null;
  private currentSessionId: string | null = null;
  private isConnected: boolean = false;
  private lastCursorPosition: number = 0;
  private ignoreNextUpdate: boolean = false;
  private participantCount: number = 1;

  constructor() {
    // Bind elements
    this.createSessionBtn = document.getElementById('create-session-btn') as HTMLButtonElement;
    this.joinSessionBtn = document.getElementById('join-session-btn') as HTMLButtonElement;
    this.leaveSessionBtn = document.getElementById('leave-session-btn') as HTMLButtonElement;
    this.sessionIdInput = document.getElementById('session-id-input') as HTMLInputElement;
    this.currentSessionIdEl = document.getElementById('current-session-id') as HTMLElement;
    this.sessionInfoEl = document.getElementById('session-info') as HTMLElement;
    this.codeEditor = document.getElementById('code-editor') as HTMLTextAreaElement;
    this.statusIndicator = document.getElementById('status') as HTMLElement;
    this.copySessionIdBtn = document.getElementById('copy-session-id') as HTMLButtonElement;
    this.notificationEl = document.getElementById('notification') as HTMLElement;
    this.participantCountEl = document.getElementById('participant-count') as HTMLElement;

    // Initialize event listeners
    this.initializeEventListeners();

    // Set initial connection status
    this.updateConnectionStatus(false);
  }

  private initializeEventListeners() {
    // Create session button
    this.createSessionBtn.addEventListener('click', () => this.createSession());

    // Join session button
    this.joinSessionBtn.addEventListener('click', () => this.joinSession());

    // Leave session button
    this.leaveSessionBtn.addEventListener('click', () => this.leaveSession());

    // Code editor input
    let debounceTimeout: number;
    this.codeEditor.addEventListener('input', () => {
      if (this.ignoreNextUpdate) {
        this.ignoreNextUpdate = false;
        return;
      }
      
      // Save cursor position
      this.lastCursorPosition = this.codeEditor.selectionStart;
      
      // Debounce to reduce network traffic
      clearTimeout(debounceTimeout);
      debounceTimeout = window.setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          const data = {
            type: 'code_update',
            content: this.codeEditor.value
          };
          this.ws.send(JSON.stringify(data));
        }
      }, 100);
    });

    // Copy session ID button
    this.copySessionIdBtn.addEventListener('click', () => this.copySessionId());

    // Handle session ID input on pressing Enter
    this.sessionIdInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.joinSessionBtn.click();
      }
    });
  }

  private showNotification(message: string, color: string = '#28a745') {
    this.notificationEl.textContent = message;
    this.notificationEl.style.backgroundColor = color;
    this.notificationEl.style.opacity = '1';
    
    setTimeout(() => {
      this.notificationEl.style.opacity = '0';
    }, 3000);
  }

  private updateConnectionStatus(connected: boolean) {
    this.isConnected = connected;
    
    if (connected) {
      this.statusIndicator.textContent = 'Connected';
      this.statusIndicator.classList.remove('disconnected');
      this.statusIndicator.classList.add('connected');
      this.codeEditor.disabled = false;
      this.leaveSessionBtn.disabled = false;
      this.createSessionBtn.disabled = true;
      this.joinSessionBtn.disabled = true;
      this.sessionIdInput.disabled = true;
      this.sessionInfoEl.style.display = 'block';
    } else {
      this.statusIndicator.textContent = 'Disconnected';
      this.statusIndicator.classList.remove('connected');
      this.statusIndicator.classList.add('disconnected');
      this.codeEditor.disabled = true;
      this.leaveSessionBtn.disabled = true;
      this.createSessionBtn.disabled = false;
      this.joinSessionBtn.disabled = false;
      this.sessionIdInput.disabled = false;
      this.sessionInfoEl.style.display = 'none';
      this.codeEditor.value = '';
      this.participantCount = 1;
      this.updateParticipantCount();
    }
  }

  private updateParticipantCount() {
    this.participantCountEl.textContent = `Participants: ${this.participantCount}`;
  }

  private async connectWebSocket(sessionId: string) {
    // Close existing socket if any
    if (this.ws) {
      this.ws.close();
    }
    
    try {
      // Determine WebSocket protocol based on page protocol
      const serverResponse = await fetch("/server-ip");
      const serverData = await serverResponse.json();
      const serverIP = serverData?.ip;
      
      this.ws = new WebSocket(`wss://${serverIP}/ws/session/${sessionId}`);
      
      this.ws.onopen = () => {
        this.currentSessionId = sessionId;
        this.currentSessionIdEl.textContent = sessionId;
        this.updateConnectionStatus(true);
        this.showNotification('Connected to session');
      };
      
      this.ws.onclose = () => {
        if (this.isConnected) {
          this.showNotification('Disconnected from session', '#dc3545');
        }
        this.updateConnectionStatus(false);
        this.currentSessionId = null;
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.showNotification('Connection error', '#dc3545');
      };
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'code_update') {
          this.ignoreNextUpdate = true;
          
          // Save cursor position
          this.lastCursorPosition = this.codeEditor.selectionStart;
          
          // Update code
          this.codeEditor.value = data.content;
          
          // Restore cursor position if possible
          if (this.lastCursorPosition <= this.codeEditor.value.length) {
            this.codeEditor.setSelectionRange(this.lastCursorPosition, this.lastCursorPosition);
          }
        } else if (data.type === 'participant_update') {
          this.participantCount = data.count;
          this.updateParticipantCount();
        }
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.showNotification('Error connecting to session', '#dc3545');
    }
  }

  private async createSession() {
    try {
      const response = await fetch('/session-id');
      const data = await response.json();
      const sessionId = data.session_id;
      
      this.connectWebSocket(sessionId);
    } catch (error) {
      console.error('Error creating session:', error);
      this.showNotification('Error creating session', '#dc3545');
    }
  }

  private joinSession() {
    const sessionId = this.sessionIdInput.value.trim();
    
    if (!sessionId) {
      this.showNotification('Please enter a session ID', '#ffc107');
      return;
    }
    
    this.connectWebSocket(sessionId);
  }

  private leaveSession() {
    if (this.ws) {
      this.ws.close();
    }
  }

  private copySessionId() {
    if (this.currentSessionId) {
      navigator.clipboard.writeText(this.currentSessionId).then(() => {
        this.showNotification('Session ID copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy: ', err);
      });
    }
  }
}

// Initialize the session manager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  new SessionManager();
});