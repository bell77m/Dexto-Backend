var peer = new Peer()
var myStream
var peerList = []

// this function will be initiating the peer
function init(userId){
  peer = new Peer(userId)
  peer.on('open',(id) => {
    console.log(id + " connected") //if we connect successfully this will print
  })

  listenToCall()
}

// this function will keep listening to call or incoming events
function listenToCall(){
  peer.on('call',(call) => {
    navigator.mediaDevices.getUserMedia({
      video: true,
      audio: true
    }).then((stream) => {

      myStream = stream
      addLocalVideo(stream)
      call.answer(stream)
      call.on('stream',(remoteStream) => {
        if(!peerList.includes(call.peer)){
          addRemoteVideo(remoteStream)
          peerList.push(call.peer)
        }
      })
    }).catch((err) => {
      console.log("unable to connect: " + err)
    })
  })
}

// make call
function makeCall(receiverId){
  // Check if getUserMedia is available and request permission
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      // This will show the permission dialog when called
      navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true
      }).then((stream) => {
          myStream = stream;
          addLocalVideo(stream);
          let call = peer.call(receiverId, stream);
          call.on('stream', (remoteStream) => {
              if (!peerList.includes(call.peer)) {
                  addRemoteVideo(remoteStream);
                  peerList.push(call.peer);
              }
          });
      }).catch((err) => {
          console.log("Unable to access media devices: ", err);
          alert("Permission denied or unable to access media devices.");
      });
  } else {
      alert("Your browser does not support WebRTC or getUserMedia.");
  }
}


// hang up the call and disconnect
function hangUpCall() {
  if(peer){
    peer.destroy();
  }

  if(myStream){
    myStream.getTracks().forEach(track => track.stop());
  }

  peerList.forEach(peerId => {
    const remoteVideo = document.getElementById(peerId);
    if(remoteVideo){
      remoteVideo.srcObject.getTracks().forEach(track => track.stop());
      remoteVideo.remove();
    }
  });
  peerList = [];

  const localVideoElement = document.querySelector("#localVideo video");
  if (localVideoElement) {
    localVideoElement.srcObject = null;
    localVideoElement.remove();
  }

  console.log("Call ended.");

  window.location.href = "/";
}

function addLocalVideo(stream){
  let video = document.createElement("video")
  video.srcObject = stream
  video.classList.add("video")
  video.muted = true
  video.play()
  document.getElementById("localVideo").append(video)
}

function addRemoteVideo(stream){
  let video = document.createElement("video")
  video.srcObject = stream
  video.classList.add("video")
  video.play()
  document.getElementById("remoteVideo").append(video)
}

// toggle the video
function toggleVideo(b){
  if(b == "true"){
    myStream.getVideoTracks()[0].enabled = true
  }
  else{
    myStream.getVideoTracks()[0].enabled = false
  }
}

// toggle audio
function toggleAudio(b){
  if(b == "true"){
    myStream.getAudioTracks()[0].enabled = true
  }
  else{
    myStream.getAudioTracks()[0].enabled = false
  }
}

// still need to use console for this, waiting for front-end
