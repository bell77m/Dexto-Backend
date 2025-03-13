import React, { useEffect, useState } from 'react';

export interface SessionScriptProps {
  onSessionConnect?: (sessionId: string) => void;
  onSessionDisconnect?: () => void;
}

export const useSessionScript = ({ 
  onSessionConnect, 
  onSessionDisconnect 
}: SessionScriptProps = {}) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [participantCount, setParticipantCount] = useState(1);
  const [notification, setNotification] = useState<{
    message: string;
    color: string;
  } | null>(null);

  // Notification function
  const showNotification = (message: string, color = '#28a745') => {
    setNotification({ message, color });
    
    setTimeout(() => {
      setNotification(null);
    }, 3000);
  };

  // Connect to WebSocket
  const connectWebSocket = async (sessionId: string) => {
    // Close existing socket if any
    if (ws) {
      ws.close();
    }
    
    try {
      // Determine WebSocket protocol based on page protocol
      const serverResponse = await fetch("/server-ip");
      const serverData = await serverResponse.json();
      const serverIP = serverData?.ip;
      
      const newWs = new WebSocket(`wss://${serverIP}/ws/session/${sessionId}`);
      
      newWs.onopen = () => {
        setCurrentSessionId(sessionId);
        setIsConnected(true);
        showNotification('Connected to session');
        
        if (onSessionConnect) {
          onSessionConnect(sessionId);
        }
      };
      
      newWs.onclose = () => {
        if (isConnected) {
          showNotification('Disconnected from session', '#dc3545');
        }
        setIsConnected(false);
        setCurrentSessionId(null);
        
        if (onSessionDisconnect) {
          onSessionDisconnect();
        }
      };
      
      newWs.onerror = (error) => {
        console.error('WebSocket error:', error);
        showNotification('Connection error', '#dc3545');
      };
      
      newWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'code_update') {
          // Emit code update event or handle in parent component
        } else if (data.type === 'participant_update') {
          setParticipantCount(data.count);
        }
      };
      
      setWs(newWs);
      
      return newWs;
    } catch (error) {
      console.error('Error creating session:', error);
      showNotification('Error creating session', '#dc3545');
      return null;
    }
  };

  // Create a new session
  const createSession = async () => {
    try {
      const response = await fetch('/session-id');
      const data = await response.json();
      const sessionId = data.session_id;
      
      return await connectWebSocket(sessionId);
    } catch (error) {
      console.error('Error creating session:', error);
      showNotification('Error creating session', '#dc3545');
      return null;
    }
  };

  // Join an existing session
  const joinSession = (sessionId: string) => {
    if (!sessionId.trim()) {
      showNotification('Please enter a session ID', '#ffc107');
      return null;
    }
    
    return connectWebSocket(sessionId);
  };

  // Leave the current session
  const leaveSession = () => {
    if (ws) {
      ws.close();
    }
  };

  // Send code update
  const sendCodeUpdate = (content: string) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      const data = {
        type: 'code_update',
        content: content
      };
      ws.send(JSON.stringify(data));
    }
  };

  // Copy session ID
  const copySessionId = () => {
    if (currentSessionId) {
      navigator.clipboard.writeText(currentSessionId).then(() => {
        showNotification('Session ID copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy: ', err);
      });
    }
  };

  return {
    ws,
    currentSessionId,
    isConnected,
    participantCount,
    notification,
    createSession,
    joinSession,
    leaveSession,
    sendCodeUpdate,
    copySessionId
  };
};

// Example React Component
export const SessionManager: React.FC<SessionScriptProps> = (props) => {
  const {
    ws,
    currentSessionId,
    isConnected,
    participantCount,
    notification,
    createSession,
    joinSession,
    leaveSession,
    copySessionId
  } = useSessionScript(props);

  const [sessionIdInput, setSessionIdInput] = useState('');
  const [codeEditorContent, setCodeEditorContent] = useState('');

  return (
    <div>
      {notification && (
        <div style={{ 
          backgroundColor: notification.color, 
          opacity: 1, 
          padding: '10px',
          color: 'white'
        }}>
          {notification.message}
        </div>
      )}
      
      <div>
        <button 
          disabled={isConnected}
          onClick={() => createSession()}
        >
          Create Session
        </button>
        
        <input 
          type="text"
          value={sessionIdInput}
          onChange={(e) => setSessionIdInput(e.target.value)}
          placeholder="Enter Session ID"
          disabled={isConnected}
        />
        
        <button 
          disabled={isConnected}
          onClick={() => joinSession(sessionIdInput)}
        >
          Join Session
        </button>
      </div>
      
      {isConnected && (
        <div>
          <p>Current Session ID: {currentSessionId}</p>
          <p>Participants: {participantCount}</p>
          
          <textarea 
            value={codeEditorContent}
            onChange={(e) => {
              setCodeEditorContent(e.target.value);
              // You might want to add debounce here
            }}
            disabled={!isConnected}
          />
          
          <button onClick={leaveSession}>Leave Session</button>
          <button onClick={copySessionId}>Copy Session ID</button>
        </div>
      )}
    </div>
  );
};