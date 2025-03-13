import React, { useState, useEffect } from 'react';

interface PeerConnection {
  peer: RTCPeerConnection;
  audioElements: HTMLAudioElement[];
}

export interface VideoCallProps {
  onStatusUpdate?: (message: string) => void;
}

export const useVideoCall = ({ onStatusUpdate }: VideoCallProps = {}) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [peerConnections, setPeerConnections] = useState<{[key: string]: PeerConnection}>({});
  const [isCallActive, setIsCallActive] = useState(false);
  const [status, setStatus] = useState<string[]>([]);

  const config: RTCConfiguration = { 
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }] 
  };

  const updateStatus = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    const newStatus = [...status, `${timestamp}: ${message}`];
    setStatus(newStatus);
    
    if (onStatusUpdate) {
      onStatusUpdate(message);
    }
    console.log(message);
  };

  const createPeerConnection = async (remotePeerId: string, data?: any) => {
    try {
      const peer = new RTCPeerConnection(config);
      
      // Add local tracks to the connection
      if (localStream) {
        localStream.getTracks().forEach(track => {
          peer.addTrack(track, localStream);
        });
      }

      // Handle remote tracks
      peer.ontrack = (event) => {
        updateStatus(`Received audio from remote peer`);
        const audio = new Audio();
        audio.srcObject = event.streams[0];
        audio.autoplay = true;

        // Update peer connections with new audio element
        setPeerConnections(prev => {
          const updatedPeer = prev[remotePeerId] || { peer, audioElements: [] };
          updatedPeer.audioElements.push(audio);
          return {
            ...prev,
            [remotePeerId]: updatedPeer
          };
        });
      };

      // Handle ICE candidates
      peer.onicecandidate = (e) => {
        if (e.candidate && ws) {
          ws.send(JSON.stringify({
            target: remotePeerId,
            candidate: e.candidate,
            sender: ws.url.split('/').pop()
          }));
        }
      };

      // Connection state monitoring
      peer.oniceconnectionstatechange = () => {
        updateStatus(`ICE connection state: ${peer.iceConnectionState}`);
      };

      // For initiating the call
      if (data && data.join) {
        const offer = await peer.createOffer();
        await peer.setLocalDescription(offer);
        ws?.send(JSON.stringify({
          target: remotePeerId,
          offer,
          sender: ws.url.split('/').pop()
        }));
      }

      return peer;
    } catch (error) {
      updateStatus(`Error creating peer connection: ${(error as Error).message}`);
      throw error;
    }
  };

  const startCall = async () => {
    try {
      updateStatus("Connecting to server...");

      // Create WebSocket connection first
      const clientId = Math.random().toString(36).substr(2, 5);
      const serverResponse = await fetch("/server-ip");
      const serverData = await serverResponse.json();
      const serverIP = serverData?.ip;

      const newWs = new WebSocket(`wss://${serverIP}:8000/ws/vc/${clientId}`);

      newWs.onopen = async () => {
        updateStatus("Connected to server. Requesting microphone access...");

        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          setLocalStream(stream);
          
          updateStatus("Microphone access granted. Waiting for peers...");
          setIsCallActive(true);
          setWs(newWs);
          
          newWs.send(JSON.stringify({ 
            join: true, 
            sender: "User" + Math.floor(Math.random() * 1000) 
          }));
        } catch (error) {
          updateStatus(`Microphone access denied: ${(error as Error).message}`);
          newWs.close();
        }
      };

      newWs.onclose = () => {
        updateStatus("Disconnected from server.");
        if (isCallActive) {
          endCall();
        }
      };

      newWs.onerror = (error) => {
        updateStatus(`WebSocket error: ${(error as Error).message}`);
      };

      newWs.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.offer) {
            updateStatus(`Received call offer from ${data.sender}`);
            await handleOffer(data);
          }
          else if (data.answer) {
            updateStatus(`Received call answer from ${data.sender}`);
            await handleAnswer(data);
          }
          else if (data.candidate) {
            await handleCandidate(data);
          }
          else if (data.join) {
            updateStatus(`${data.sender} joined. Initiating call...`);
            await createPeerConnection(data.sender, data);
          }
        } catch (error) {
          updateStatus(`Error processing message: ${(error as Error).message}`);
          console.error("Message processing error:", error);
        }
      };

      return newWs;
    } catch (error) {
      updateStatus(`Error starting call: ${(error as Error).message}`);
      return null;
    }
  };

  const handleOffer = async (data: any) => {
    try {
      const peer = await createPeerConnection(data.sender, data);
      const peerInstance = peer as RTCPeerConnection;
      
      await peerInstance.setRemoteDescription(new RTCSessionDescription(data.offer));
      const answer = await peerInstance.createAnswer();
      await peerInstance.setLocalDescription(answer);
      
      ws?.send(JSON.stringify({ 
        target: data.sender, 
        answer, 
        sender: ws?.url.split('/').pop() 
      }));
    } catch (error) {
      updateStatus(`Error handling offer: ${(error as Error).message}`);
    }
  };

  const handleAnswer = async (data: any) => {
    try {
      const peerConnection = peerConnections[data.sender];
      if (peerConnection) {
        await peerConnection.peer.setRemoteDescription(
          new RTCSessionDescription(data.answer)
        );
        updateStatus("Call connected!");
      } else {
        updateStatus(`No peer connection found for ${data.sender}`);
      }
    } catch (error) {
      updateStatus(`Error handling answer: ${(error as Error).message}`);
    }
  };

  const handleCandidate = async (data: any) => {
    try {
      const peerConnection = peerConnections[data.sender];
      if (peerConnection) {
        await peerConnection.peer.addIceCandidate(
          new RTCIceCandidate(data.candidate)
        );
      }
    } catch (error) {
      updateStatus(`Error handling ICE candidate: ${(error as Error).message}`);
    }
  };

  const endCall = () => {
    updateStatus("Ending call...");
    setIsCallActive(false);

    // Close all peer connections
    Object.values(peerConnections).forEach((connection) => {
      try {
        // Stop all remote audio elements
        connection.audioElements.forEach(audio => {
          try {
            audio.pause();
            audio.srcObject = null;
          } catch (e) {
            console.error("Error stopping audio:", e);
          }
        });
        connection.peer.close();
      } catch (e) {
        console.error("Error closing peer connection:", e);
      }
    });

    // Clear peer connections
    setPeerConnections({});

    // Stop local media tracks
    if (localStream) {
      try {
        localStream.getTracks().forEach(track => track.stop());
        setLocalStream(null);
      } catch (e) {
        console.error("Error stopping local stream:", e);
      }
    }

    // Close WebSocket
    if (ws) {
      try {
        ws.close();
        setWs(null);
      } catch (e) {
        console.error("Error closing WebSocket:", e);
      }
    }
  };

  return {
    startCall,
    endCall,
    isCallActive,
    status,
    localStream
  };
};

// Example React Component
export const VideoCallComponent: React.FC<VideoCallProps> = (props) => {
  const {
    startCall,
    endCall,
    isCallActive,
    status,
    localStream
  } = useVideoCall(props);

  return (
    <div>
      <div>
        <button 
          onClick={startCall} 
          disabled={isCallActive}
        >
          Start Call
        </button>
        
        <button 
          onClick={endCall} 
          disabled={!isCallActive}
        >
          End Call
        </button>
      </div>

      {localStream && (
        <div>
          <p>Local audio stream active</p>
        </div>
      )}

      <div>
        <h3>Call Status:</h3>
        <ul>
          {status.map((statusMsg, index) => (
            <li key={index}>{statusMsg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};