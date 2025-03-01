let peer;
let ws;
let peers = {};
let localStream = null;
let response;
let data;
let serverIP;

async function connect_ws(userId) {
    response = await fetch("/server-ip");
    data = await response.json();
    serverIP = data.ip;
    ws = new WebSocket(`ws://${serverIP}:8000/ws/vc/${userId}`);

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === "peer-connect") {
            if (!peers[message.peer_id]) {
                connectToPeer(message.peer_id);
            }
        } else if (message.type === "peer-disconnect") {
            removeAudio(message.peer_id);
        }
    };

    ws.onopen = () => {
        console.log("WebSocket connection established.");
        ws.send(JSON.stringify({ type: "peer-connect", target: "all", peer_id: userId }));
        console.log("ready state: " + ws.readyState)
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        console.error("Error details:", {
            target: error.target,
            isTrusted: error.isTrusted,
            currentTarget: error.currentTarget,
            eventPhase: error.eventPhase
        });
    };

    ws.onclose = () => {
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

    navigator.mediaDevices.getUserMedia({
        audio: {
            autoGainControl: true,
            echoCancellation: true,
            noiseSuppression: true,
        }
    }).then((stream) => {
        if (stream && stream.active) {
            localStream = stream;
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
    if (stream && stream.active) {
        let audioContext = new (window.AudioContext || window.webkitAudioContext)();
        let source = audioContext.createMediaStreamSource(stream);
        let gainNode = audioContext.createGain();

        gainNode.gain.value = 1.5; // Adjust volume (default 1.0)

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

    for (let peerId in peers) {
        if (peers[peerId]) {
            peers[peerId].close();
            removeAudio(peerId);
        }
    }
    peers = {};

    console.log("Call ended.");
}
