
let CURRENT_ROOM = null;

// Define socket after CURRENT_USER is available
//const socket = io({ query: { username: CURRENT_USER } });

const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("messageInput");
const messagesDiv = document.getElementById("messages");
const chatList = document.getElementById("chatList");
const roomList = document.getElementById("roomList");
const chatTitle = document.getElementById("chatTitle");

// Toggle Group Form
document.getElementById("toggleRoomFormBtn").addEventListener("click", () => {
    const form = document.getElementById("roomForm");
    form.style.display = form.style.display === "none" ? "block" : "none";
});
// Load joined groups
socket.on("group_list_update", (groups) => {
    roomList.innerHTML = "";
    groups.forEach(room => {
        const li = document.createElement("li");
        li.textContent = room;
        li.classList.add("group-item");

        li.addEventListener("click", () => {
            CURRENT_ROOM = room;
            TO_USER = null;
            chatTitle.textContent = `Group: ${room}`;
            messagesDiv.innerHTML = "";


            socket.emit("join_room", { room, username: CURRENT_USER });
            console.log("Joining room:", room);

            fetch(`/room-history/${room}`)
                .then(res => res.json())
                .then(data => {
                    data.forEach(msg => {
                        const msgDiv = document.createElement("div");
                        msgDiv.classList.add("message");
                        msgDiv.classList.add(msg.sender === CURRENT_USER ? "sent" : "received");
                        msgDiv.innerHTML = `<strong>${msg.sender}:</strong> ${msg.message}`;
                        messagesDiv.appendChild(msgDiv);
                    });
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                });
        });

        roomList.appendChild(li);
    });
});
// Create or Join Group
document.getElementById("joinRoomBtn").addEventListener("click", () => {
    const room = document.getElementById("roomInput").value.trim();
    if (room) {
        socket.emit("create_or_join_group", {
            group: room,
            username: CURRENT_USER
        });

        CURRENT_ROOM = room;
        TO_USER = null;
        chatTitle.textContent = `Group: ${room}`;
        messagesDiv.innerHTML = "";

        fetch(`/room-history/${room}`)
            .then(res => res.json())
            .then(data => {
                data.forEach(msg => {
                    const msgDiv = document.createElement("div");
                    msgDiv.classList.add("message");
                    msgDiv.classList.add(msg.sender === CURRENT_USER ? "sent" : "received");
                    msgDiv.innerHTML = `<strong>${msg.sender}:</strong> ${msg.message}`;
                    messagesDiv.appendChild(msgDiv);
                });
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            });
    }
});

// On connect, get user list and group list
socket.on("connect", () => {
    socket.emit("get_users", { current_user: CURRENT_USER });
    socket.emit("get_groups", { username: CURRENT_USER });  // ✅ Load joined groups
});

// Load user list for direct messages
socket.on("user_list", (users) => {
    chatList.innerHTML = "";
    users.forEach(user => {
        const li = document.createElement("li");
        li.textContent = user;
        li.classList.add("chat-user");

        li.addEventListener("click", () => {
            TO_USER = user;
            CURRENT_ROOM = null;
            chatTitle.textContent = `Chat with ${user}`;
            messagesDiv.innerHTML = "";


            fetch(`/chat-history/${user}`)
                .then(res => res.json())
                .then(messages => {
                    messages.forEach(data => {
                        const msgDiv = document.createElement("div");
                        msgDiv.classList.add("message");
                        msgDiv.classList.add(data.from_user === CURRENT_USER ? "sent" : "received");
                        msgDiv.innerHTML = `<strong>${data.from_user}:</strong> ${data.message}`;
                        messagesDiv.appendChild(msgDiv);
                    });
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                });

            document.querySelectorAll(".chat-user").forEach(el => el.classList.remove("selected"));
            li.classList.add("selected");
        });

        chatList.appendChild(li);
    });
});



// Send button
sendBtn.addEventListener("click", () => {
    const msg = messageInput.value.trim();
    if (!msg) return;

    if (CURRENT_ROOM) {
        socket.emit("send_group_message", {
            sender: CURRENT_USER,
            room: CURRENT_ROOM,
            message: msg
        });
    } else if (TO_USER) {
        socket.emit("send_message", {
            from_user: CURRENT_USER,
            to_user: TO_USER,
            message: msg
        });
    }

    messageInput.value = "";
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
});

// 1-on-1 message received
socket.on("receive_message", (data) => {
    const isRelevant =
        (data.from_user === CURRENT_USER && data.to_user === TO_USER) ||
        (data.from_user === TO_USER && data.to_user === CURRENT_USER);

    if (isRelevant) {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message");
        msgDiv.classList.add(data.from_user === CURRENT_USER ? "sent" : "received");
        msgDiv.innerHTML = `<strong>${data.from_user}:</strong> ${data.message}`;
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
});

// Group message received
socket.on("receive_group_message", (data) => {
    if (data.room === CURRENT_ROOM) {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message");
        msgDiv.classList.add(data.sender === CURRENT_USER ? "sent" : "received");
        msgDiv.innerHTML = `<strong>${data.sender}:</strong> ${data.message}`;
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
});
