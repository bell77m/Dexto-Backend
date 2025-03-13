import React, { useState, useEffect } from 'react';

export interface ChatMessage {
  id: number;
  text: string;
}

export interface TextChatProps {
  onMessageReceived?: (message: string) => void;
}

export const useTextChat = ({ onMessageReceived }: TextChatProps = {}) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [clientId, setClientId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');

  const startWebSocket = async () => {
    try {
      const newClientId = Date.now();
      setClientId(newClientId);

      const serverResponse = await fetch("/server-ip");
      const serverData = await serverResponse.json();
      const serverIP = serverData?.ip;

      const newWs = new WebSocket(`wss://${serverIP}:8000/ws/${newClientId}`);

      newWs.onopen = () => {
        console.log("Connected to WebSocket at:", serverIP);
      };

      newWs.onmessage = (event) => {
        const newMessage: ChatMessage = {
          id: Date.now(),
          text: event.data
        };
        setMessages(prevMessages => [...prevMessages, newMessage]);
        
        if (onMessageReceived) {
          onMessageReceived(event.data);
        }
      };

      newWs.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      setWs(newWs);
    } catch (error) {
      console.error("Error establishing WebSocket:", error);
    }
  };

  useEffect(() => {
    startWebSocket();

    // Cleanup function
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const sendMessage = () => {
    if (ws && ws.readyState === WebSocket.OPEN && inputMessage.trim()) {
      ws.send(inputMessage);
      setInputMessage('');
    }
  };

  return {
    clientId,
    messages,
    inputMessage,
    setInputMessage,
    sendMessage
  };
};

// Example React Component
export const TextChatComponent: React.FC<TextChatProps> = (props) => {
  const {
    clientId,
    messages,
    inputMessage,
    setInputMessage,
    sendMessage
  } = useTextChat(props);

  return (
    <div>
      <div>Client ID: {clientId}</div>
      <ul>
        {messages.map((msg) => (
          <li key={msg.id}>{msg.text}</li>
        ))}
      </ul>
      <input 
        type="text"
        value={inputMessage}
        onChange={(e) => setInputMessage(e.target.value)}
        placeholder="Type a message"
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
};