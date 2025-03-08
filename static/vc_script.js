let ws;
let peerConnections = {};
const config = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };
let localStream = null;
let isCallActive = false;

function updateStatus(message) {
    const statusDiv = document.getElementById('statusDiv');
    const timestamp = new Date().toLocaleTimeString();
    statusDiv.innerHTML += `<div>${timestamp}: ${message}</div>`;
    console.log(message);
}

async function startCall() {
    try {
        document.getElementById('startButton').disabled = true;
        updateStatus("Connecting to server...");

        // Create WebSocket connection first
        const clientId = Math.random().toString(36).substr(2, 5);
        let response = await fetch("/server-ip");
        let data = await response.json();
        let serverIP = data.ip;
        ws = new WebSocket(`wss://${serverIP}:8000/ws/vc/${clientId}`);

        ws.onopen = async () => {
            updateStatus("Connected to server. Requesting microphone access...");

            try {
                localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                updateStatus("Microphone access granted. Waiting for peers...");
                isCallActive = true;
                document.getElementById('endButton').disabled = false;
                ws.send(JSON.stringify({ join: true, sender: "User" + Math.floor(Math.random() * 1000) }));
            } catch (error) {
                updateStatus(`Microphone access denied: ${error.message}`);
                document.getElementById('startButton').disabled = false;
                ws.close();
            }
        };

        ws.onclose = () => {
            updateStatus("Disconnected from server.");
            if (isCallActive) {
                endCall();
            }
        };

        ws.onerror = (error) => {
            updateStatus(`WebSocket error: ${error.message || "Unknown error"}`);
            document.getElementById('startButton').disabled = false;
        };

        ws.onmessage = async (event) => {
            try {
                let data = JSON.parse(event.data);

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
                    await createPeerConnection(data.sender, data); // Pass `data` as an argument
                }
            } catch (error) {
                updateStatus(`Error processing message: ${error.message}`);
                console.error("Message processing error:", error);
            }
        };
    } catch (error) {
        updateStatus(`Error starting call: ${error.message}`);
        console.error("Start call error:", error);
        document.getElementById('startButton').disabled = false;
    }
}

async function handleOffer(data) {
    try {
        let peer = await createPeerConnection(data.sender, data); // Pass `data` as an argument
        await peer.setRemoteDescription(new RTCSessionDescription(data.offer));
        let answer = await peer.createAnswer();
        await peer.setLocalDescription(answer);
        ws.send(JSON.stringify({ target: data.sender, answer, sender: ws.url.split('/').pop() }));
    } catch (error) {
        updateStatus(`Error handling offer: ${error.message}`);
        console.error("Handle offer error:", error);
    }
}

async function handleAnswer(data) {
    try {
        const peer = peerConnections[data.sender];
        if (peer) {
            await peer.setRemoteDescription(new RTCSessionDescription(data.answer));
            updateStatus("Call connected!");
        } else {
            updateStatus(`No peer connection found for ${data.sender}`);
        }
    } catch (error) {
        updateStatus(`Error handling answer: ${error.message}`);
        console.error("Handle answer error:", error);
    }
}

async function handleCandidate(data) {
    try {
        const peer = peerConnections[data.sender];
        if (peer) {
            await peer.addIceCandidate(new RTCIceCandidate(data.candidate));
        }
    } catch (error) {
        updateStatus(`Error handling ICE candidate: ${error.message}`);
        console.error("Handle candidate error:", error);
    }
}

async function createPeerConnection(remotePeerId, data) {
    try {
        const peer = new RTCPeerConnection(config);
        peerConnections[remotePeerId] = peer;

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

            // Store the audio element to prevent garbage collection
            if (!peer.audioElements) {
                peer.audioElements = [];
            }
            peer.audioElements.push(audio);
        };

        // Handle ICE candidates
        peer.onicecandidate = (e) => {
            if (e.candidate) {
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
            ws.send(JSON.stringify({
                target: remotePeerId,
                offer,
                sender: ws.url.split('/').pop()
            }));
        }

        return peer;
    } catch (error) {
        updateStatus(`Error creating peer connection: ${error.message}`);
        console.error("Create peer connection error:", error);
        throw error;
    }
}

function endCall() {
    updateStatus("Ending call...");
    isCallActive = false;

    // Close all peer connections
    Object.entries(peerConnections).forEach(([peerId, peer]) => {
        if (peer) {
            try {
                // Stop all remote audio elements
                if (peer.audioElements) {
                    peer.audioElements.forEach(audio => {
                        try {
                            audio.pause();
                            audio.srcObject = null;
                        } catch (e) {
                            console.error("Error stopping audio:", e);
                        }
                    });
                }
                peer.close();
            } catch (e) {
                console.error("Error closing peer connection:", e);
            }
        }
        delete peerConnections[peerId]; // Remove the peer from the connections object
    });

    // Stop local media tracks
    if (localStream) {
        try {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        } catch (e) {
            console.error("Error stopping local stream:", e);
        }
    }

    // Close WebSocket
    if (ws) {
        try {
            ws.close();
            ws = null;
        } catch (e) {
            console.error("Error closing WebSocket:", e);
        }
    }

    // Reset UI
    document.getElementById('startButton').disabled = false;
    document.getElementById('endButton').disabled = true;
    updateStatus("Call ended. You can start a new call.");
}