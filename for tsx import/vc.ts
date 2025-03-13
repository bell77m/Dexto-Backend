export class VideoCallManager {
  // HTML Elements
  private startButton: HTMLButtonElement;
  private endButton: HTMLButtonElement;
  private statusDiv: HTMLDivElement;

  // WebRTC and WebSocket Configuration
  private config: RTCConfiguration = { 
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }] 
  };

  // State Variables
  private ws: WebSocket | null = null;
  private peerConnections: { [key: string]: {
    peer: RTCPeerConnection;
    audioElements: HTMLAudioElement[];
  } } = {};
  private localStream: MediaStream | null = null;
  private isCallActive: boolean = false;

  constructor() {
    // Bind HTML Elements
    this.startButton = document.getElementById('startButton') as HTMLButtonElement;
    this.endButton = document.getElementById('endButton') as HTMLButtonElement;
    this.statusDiv = document.getElementById('statusDiv') as HTMLDivElement;

    // Initialize Event Listeners
    this.initializeEventListeners();
  }

  private initializeEventListeners() {
    this.startButton.addEventListener('click', () => this.startCall());
    this.endButton.addEventListener('click', () => this.endCall());
    this.endButton.disabled = true;
  }

  private updateStatus(message: string) {
    const timestamp = new Date().toLocaleTimeString();
    const statusEntry = document.createElement('div');
    statusEntry.textContent = `${timestamp}: ${message}`;
    this.statusDiv.appendChild(statusEntry);
    console.log(message);
  }

  private async startCall() {
    try {
      this.startButton.disabled = true;
      this.updateStatus("Connecting to server...");

      // Create WebSocket connection
      const clientId = Math.random().toString(36).substr(2, 5);
      const serverResponse = await fetch("/server-ip");
      const serverData = await serverResponse.json();
      const serverIP = serverData?.ip;

      this.ws = new WebSocket(`wss://${serverIP}:8000/ws/vc/${clientId}`);

      this.ws.onopen = async () => {
        this.updateStatus("Connected to server. Requesting microphone access...");

        try {
          this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          this.updateStatus("Microphone access granted. Waiting for peers...");
          this.isCallActive = true;
          this.endButton.disabled = false;
          
          this.ws?.send(JSON.stringify({ 
            join: true, 
            sender: "User" + Math.floor(Math.random() * 1000) 
          }));
        } catch (error) {
          this.updateStatus(`Microphone access denied: ${(error as Error).message}`);
          this.ws?.close();
          this.startButton.disabled = false;
        }
      };

      this.ws.onclose = () => {
        this.updateStatus("Disconnected from server.");
        if (this.isCallActive) {
          this.endCall();
        }
      };

      this.ws.onerror = (error) => {
        this.updateStatus(`WebSocket error: ${error}}`);
        this.startButton.disabled = false;
      };

      this.ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.offer) {
            this.updateStatus(`Received call offer from ${data.sender}`);
            await this.handleOffer(data);
          }
          else if (data.answer) {
            this.updateStatus(`Received call answer from ${data.sender}`);
            await this.handleAnswer(data);
          }
          else if (data.candidate) {
            await this.handleCandidate(data);
          }
          else if (data.join) {
            this.updateStatus(`${data.sender} joined. Initiating call...`);
            await this.createPeerConnection(data.sender, data);
          }
        } catch (error) {
          this.updateStatus(`Error processing message: ${(error as Error).message}`);
          console.error("Message processing error:", error);
        }
      };
    } catch (error) {
      this.updateStatus(`Error starting call: ${(error as Error).message}`);
      this.startButton.disabled = false;
    }
  }

  private async createPeerConnection(remotePeerId: string, data?: any) {
    try {
      const peer = new RTCPeerConnection(this.config);
      
      // Store peer connection
      this.peerConnections[remotePeerId] = { 
        peer, 
        audioElements: [] 
      };

      // Add local tracks to the connection
      if (this.localStream) {
        this.localStream.getTracks().forEach(track => {
          peer.addTrack(track, this.localStream!);
        });
      }

      // Handle remote tracks
      peer.ontrack = (event) => {
        this.updateStatus(`Received audio from remote peer`);
        const audio = new Audio();
        audio.srcObject = event.streams[0];
        audio.autoplay = true;

        // Store audio element
        this.peerConnections[remotePeerId].audioElements.push(audio);
      };

      // Handle ICE candidates
      peer.onicecandidate = (e) => {
        if (e.candidate && this.ws) {
          this.ws.send(JSON.stringify({
            target: remotePeerId,
            candidate: e.candidate,
            sender: this.ws.url.split('/').pop()
          }));
        }
      };

      // Connection state monitoring
      peer.oniceconnectionstatechange = () => {
        this.updateStatus(`ICE connection state: ${peer.iceConnectionState}`);
      };

      // For initiating the call
      if (data && data.join) {
        const offer = await peer.createOffer();
        await peer.setLocalDescription(offer);
        this.ws?.send(JSON.stringify({
          target: remotePeerId,
          offer,
          sender: this.ws?.url.split('/').pop()
        }));
      }

      return peer;
    } catch (error) {
      this.updateStatus(`Error creating peer connection: ${(error as Error).message}`);
      throw error;
    }
  }

  private async handleOffer(data: any) {
    try {
      const peer = await this.createPeerConnection(data.sender, data);
      await peer.setRemoteDescription(new RTCSessionDescription(data.offer));
      const answer = await peer.createAnswer();
      await peer.setLocalDescription(answer);
      
      this.ws?.send(JSON.stringify({ 
        target: data.sender, 
        answer, 
        sender: this.ws?.url.split('/').pop() 
      }));
    } catch (error) {
      this.updateStatus(`Error handling offer: ${(error as Error).message}`);
    }
  }

  private async handleAnswer(data: any) {
    try {
      const peerConnection = this.peerConnections[data.sender];
      if (peerConnection) {
        await peerConnection.peer.setRemoteDescription(
          new RTCSessionDescription(data.answer)
        );
        this.updateStatus("Call connected!");
      } else {
        this.updateStatus(`No peer connection found for ${data.sender}`);
      }
    } catch (error) {
      this.updateStatus(`Error handling answer: ${(error as Error).message}`);
    }
  }

  private async handleCandidate(data: any) {
    try {
      const peerConnection = this.peerConnections[data.sender];
      if (peerConnection) {
        await peerConnection.peer.addIceCandidate(
          new RTCIceCandidate(data.candidate)
        );
      }
    } catch (error) {
      this.updateStatus(`Error handling ICE candidate: ${(error as Error).message}`);
    }
  }

  private endCall() {
    this.updateStatus("Ending call...");
    this.isCallActive = false;

    // Close all peer connections
    Object.entries(this.peerConnections).forEach(([peerId, connection]) => {
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
    this.peerConnections = {};

    // Stop local media tracks
    if (this.localStream) {
      try {
        this.localStream.getTracks().forEach(track => track.stop());
        this.localStream = null;
      } catch (e) {
        console.error("Error stopping local stream:", e);
      }
    }

    // Close WebSocket
    if (this.ws) {
      try {
        this.ws.close();
        this.ws = null;
      } catch (e) {
        console.error("Error closing WebSocket:", e);
      }
    }

    // Reset UI
    this.startButton.disabled = false;
    this.endButton.disabled = true;
    this.updateStatus("Call ended. You can start a new call.");
  }
}

// Initialize the video call manager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  new VideoCallManager();
});