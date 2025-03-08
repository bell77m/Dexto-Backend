let client_id = Date.now();
document.querySelector("#ws-id").textContent = client_id;

async function startWebSocket() {
    try {
        let response = await fetch("/server-ip");
        let data = await response.json();
        let serverIP = data.ip;
        let ws = new WebSocket(`ws://${serverIP}:8000/ws/${client_id}`);
        console.log("connected to WebSocket at:", serverIP);

        ws.onmessage = function(event) {
            let messages = document.getElementById('messages');
            let message = document.createElement('li');
            let content = document.createTextNode(event.data);
            message.appendChild(content);
            messages.appendChild(message);
        };

        window.sendMessage = function(event) {
            let input = document.getElementById("messageText");
            ws.send(input.value);
            input.value = '';
            event.preventDefault();
        };
    } catch (error) {
        console.error("Error fetching server IP:", error);
    }
}

void startWebSocket();