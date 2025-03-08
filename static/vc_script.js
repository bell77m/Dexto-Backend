let peer;
let ws;
const peers = {}; // Store peer connections
let localStream = null;

// WebSocket Connection
async function connectToWebsocket(userId) {
    let response = await fetch("/server-ip");
    let data = await response.json();
    const serverIP = data.ip;

    ws = new WebSocket(`ws://${serverIP}:8000/ws/vc/${userId}`);

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === "peer-list") {
            // When a new user joins, get a list of connected peers
            message.peers.forEach(peerId => {
                if (!peers[peerId] && peerId !== userId) {
                    connectToPeer(peerId);
                }
            });
        }
        else if (message.type === "peer-connect") {
            // A new user joined, connect to them
            if (!peers[message.peer_id]) {
                connectToPeer(message.peer_id);
            }
        }
        else if (message.type === "peer-disconnect") {
            // A user left, remove them
            removePeer(message.peer_id);
        }
    };

    ws.onopen = () => {
        console.log("WebSocket connection established.");
        ws.send(JSON.stringify({ type: "join", user_id: userId }));
    };

    ws.onclose = () => {
        console.log("WebSocket connection closed.");
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

// session ID
const userId = Math.random().toString(36).substring(7);
// Start the WebRTC Call
async function startCall() {
    peer = new Peer(userId);
    
    await connectToWebsocket(userId);

    peer.on("open", (id) => {
        console.log("Connected with ID:", id);
    });

    // Handle incoming calls
    peer.on("call", (call) => {
        navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
            call.answer(stream);
            call.on("stream", (remoteStream) => {
                addAudio(remoteStream, call.peer);
            });
        }).catch((error) => {
            console.error("Error getting user media for incoming call:", error);
        });
    });

    // Get local audio stream
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
        localStream = stream;
        addAudio(localStream, "local");
    }).catch((error) => {
        console.error("Error accessing media devices:", error);
    });
}

// Connect to an existing peer
function connectToPeer(peerId) {
    if (!localStream) {
        console.error("Local stream not available, cannot call peer:", peerId);
        return;
    }

    let call = peer.call(peerId, localStream);
    if (!call) {
        console.error("Failed to call peer:", peerId);
        return;
    }

    call.on("stream", (remoteStream) => {
        addAudio(remoteStream, peerId);
    });

    peers[peerId] = call;
}

// Add Audio to Page
function addAudio(stream, peerId) {
    let existingAudio = document.getElementById(peerId);
    if (!existingAudio) {
        let audioElement = document.createElement("audio");
        audioElement.id = peerId;
        audioElement.srcObject = stream;
        audioElement.autoplay = true;
        audioElement.controls = false;
        document.body.appendChild(audioElement);
    }
}

// Remove a Peer When Disconnected
function removePeer(peerId) {
    if (peers[peerId]) {
        peers[peerId].close();
        delete peers[peerId];
    }
    
    let audioElement = document.getElementById(peerId);
    if (audioElement) {
        audioElement.remove();
    }

    console.log("Removed peer:", peerId);
}

// Leave Call
function leaveCall() {
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }

    if (ws) {
        ws.close();
        ws = null;
    }

    if (peer) {
        peer.destroy();
        peer = null;
    }

    console.log("Call ended.");
}