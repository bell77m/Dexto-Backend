let peer;
let socket;
let peers = {};
let localStream = null;

async function connect_ws(userId) {
    // Create a WebSocket connection for the given user
    socket = new WebSocket(`ws://localhost:8000/ws/vc/${userId}`);

    // Handle incoming messages from WebSocket
    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === "peer-connect") {
            if (!peers[message.peer_id]) {
                connectToPeer(message.peer_id);
            }
        } else if (message.type === "peer-disconnect") {
            removeAudio(message.peer_id);
        }
    };

    socket.onopen = () => {
        console.log("WebSocket connection established.");
        console.log(socket.readyState)
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        console.error("Error details:", {
            target: error.target,
            isTrusted: error.isTrusted,
            currentTarget: error.currentTarget,
            eventPhase: error.eventPhase
        });
    };

    socket.onclose = () => {
        console.log("WebSocket connection closed.");
    };
}

async function startCall() {
    const userId = Math.random().toString(36);
    peer = new Peer(userId);

    await connect_ws(userId);
    console.log("connected with ID: " + userId);

    peer.on("open", (id) => {
        console.log("Connected with ID:", id);
        socket.send(JSON.stringify({ type: "peer-connect", target: "all", peer_id: userId }));
    });

    peer.on("call", (call) => {
        navigator.mediaDevices.getUserMedia({
            audio: {
                autoGainControl: true,
                echoCancellation: true,
                noiseSuppression: true,
            }
        }).then((stream) => {
            call.answer(stream);
            call.on("stream", (remoteStream) => {
                addAudio(remoteStream, call.peer);
            });
        }).catch((error) => {
            console.error("Error getting user media for incoming call:", error);
        });
    });

    // Get the local stream and start the call
    navigator.mediaDevices.getUserMedia({
        audio: {
            autoGainControl: true,
            echoCancellation: true,
            noiseSuppression: true,
        }
    }).then((stream) => {
        // Check if the stream is valid before proceeding
        if (stream && stream.active) {
            localStream = stream; // Store the local stream
            addAudio(localStream, "local");
        } else {
            console.error("Local media stream is not valid or has been stopped.");
        }
    }).catch((error) => {
        console.error("Error accessing media devices:", error);
    });
}

function connectToPeer(peerId) {
    if (!localStream || !localStream.active) {
        console.error("No valid local stream available for connection.");
        return;
    }

    const call = peer.call(peerId, localStream);
    call.on("stream", (remoteStream) => {
        addAudio(remoteStream, peerId);
    });
    peers[peerId] = call;
}

function addAudio(stream, peerId) {
    // Ensure the stream is still active
    if (stream && stream.active) {
        let audioContext = new (window.AudioContext || window.webkitAudioContext)();
        let source = audioContext.createMediaStreamSource(stream);
        let gainNode = audioContext.createGain();

        gainNode.gain.value = 1.5; // Adjust volume if needed

        source.connect(gainNode);
        gainNode.connect(audioContext.destination);

        let audio = document.createElement("audio");
        audio.srcObject = stream;
        audio.autoplay = true;
        audio.id = peerId;
        document.getElementById("audioContainer").appendChild(audio);
    } else {
        console.error("The media stream is no longer valid or has been stopped.");
    }
}

function removeAudio(peerId) {
    const audioElement = document.getElementById(peerId);
    if (audioElement) {
        audioElement.remove();
    }
}

function stopLocalStream() {
    // Stop local media stream if it's available
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null; // Clear the reference
    }
}

function leaveCall() {
    if (peer) {
        peer.destroy();
        peer = null;
    }

    // Stop all active audio tracks of connected peers
    for (let peerId in peers) {
        if (peers[peerId]) {
            peers[peerId].close();
            removeAudio(peerId);
        }
    }
    peers = {}; // Clear the peer list

    // Stop local media stream
    stopLocalStream();

    // Close WebSocket connection
    if (socket) {
        socket.close();
        socket = null;
    }

    console.log("Call ended.");
}
