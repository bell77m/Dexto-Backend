const serverUrl = "ws://localhost:8000/ws/";
let peer;
let socket;
let peers = {};

async function startCall() {
    const userId = Math.random().toString(36).substr(2, 9);
    peer = new Peer(userId);
    socket = new WebSocket(serverUrl + userId);

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
        });
    });

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

    navigator.mediaDevices.getUserMedia({ 
        audio: {        
            autoGainControl: true,
            echoCancellation: true,
            noiseSuppression: true,
        } 
    }).then((stream) => {
        addAudio(stream, "local");
        socket.send(JSON.stringify({ type: "peer-connect", target: "all", peer_id: userId }));
    });
}

function connectToPeer(peerId) {
    navigator.mediaDevices.getUserMedia({ 
        audio: {        
            autoGainControl: true,  // Let browser manage safe levels
            echoCancellation: true,
            noiseSuppression: true,
        } 
     }).then((stream) => {
        const call = peer.call(peerId, stream);
        call.on("stream", (remoteStream) => {
            addAudio(remoteStream, peerId);
        });
        peers[peerId] = call;
    });
}

function addAudio(stream, peerId) {
    let audioContext = new (window.AudioContext || window.webkitAudioContext)();
    let source = audioContext.createMediaStreamSource(stream);
    let gainNode = audioContext.createGain();
    
    gainNode.gain.value = 1.5; 

    source.connect(gainNode);
    gainNode.connect(audioContext.destination);

    let audio = document.createElement("audio");
    audio.srcObject = stream;
    audio.autoplay = true;
    audio.id = peerId;
    document.getElementById("audioContainer").appendChild(audio);
}  

function removeAudio(peerId) {
    const audioElement = document.getElementById(peerId);
    if (audioElement) {
        audioElement.remove();
    }
}

function leaveCall() {
    if (peer) {
        peer.destroy();
        peer = null;
    }

    // Stop all active audio tracks
    for (let peerId in peers) {
        if (peers[peerId]) {
            peers[peerId].close();
            removeAudio(peerId);
        }
    }
    peers = {}; // Clear the peer list

    // Stop local media stream
    let localAudio = document.getElementById("local");
    if (localAudio && localAudio.srcObject) {
        localAudio.srcObject.getTracks().forEach(track => track.stop());
        localAudio.remove();
    }

    // Close WebSocket connection
    if (socket) {
        socket.close();
        socket = null;
    }

    console.log("Call ended.");
}