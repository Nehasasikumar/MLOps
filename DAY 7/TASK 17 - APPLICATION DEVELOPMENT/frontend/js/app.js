const loginBtn = document.getElementById("loginBtn");

if (loginBtn) {
    loginBtn.addEventListener("click", () => {
        window.location.href = "../chatbot.html";
    });
}

const signupBtn = document.getElementById("signupBtn");

if (signupBtn) {
    signupBtn.addEventListener("click", () => {
        window.location.href = "../chatbot.html";
    });
}

const sendBtn = document.querySelector(".send-btn");

if (sendBtn) {
    sendBtn.addEventListener("click", sendMessage);
}

async function sendMessage() {

    const input =
        document.getElementById("messageInput");

    const chatArea =
        document.getElementById("chatArea");

    const text =
        input.value.trim();

    if (text === "") return;

    // USER MESSAGE

    const userMessage =
        document.createElement("div");

    userMessage.classList.add(
        "message",
        "user"
    );

    userMessage.innerText = text;

    chatArea.appendChild(
        userMessage
    );

    input.value = "";

    chatArea.scrollTop =
        chatArea.scrollHeight;

    // BOT LOADING MESSAGE

    const loadingMessage =
        document.createElement("div");

    loadingMessage.classList.add(
        "message",
        "bot"
    );

    loadingMessage.id =
        "loadingMessage";

    loadingMessage.innerHTML =
        "Analyzing machine condition...";

    chatArea.appendChild(
        loadingMessage
    );

    chatArea.scrollTop =
        chatArea.scrollHeight;

    try {

        const response =
            await fetch(
                "http://127.0.0.1:5000/predict",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        message: text
                    })
                }
            );

        const data =
            await response.json();

        // REMOVE LOADING

        const loading =
            document.getElementById(
                "loadingMessage"
            );

        if (loading) {
            loading.remove();
        }

        // BOT RESPONSE

        const botMessage =
            document.createElement("div");

        botMessage.classList.add(
            "message",
            "bot"
        );

        botMessage.innerHTML = `
            <strong>Machine Analysis Result</strong>
            <br><br>

            <b>Status:</b>
            ${data.status}
            <br><br>

            <b>Action:</b>
            ${data.action}
        `;

        chatArea.appendChild(
            botMessage
        );

        chatArea.scrollTop =
            chatArea.scrollHeight;

    } catch (error) {

        const loading =
            document.getElementById(
                "loadingMessage"
            );

        if (loading) {
            loading.remove();
        }

        const errorMessage =
            document.createElement("div");

        errorMessage.classList.add(
            "message",
            "bot"
        );

        errorMessage.innerHTML = `
            <strong>Error</strong>
            <br><br>
            Unable to connect to backend.
            <br>
            Make sure Flask server is running.
        `;

        chatArea.appendChild(
            errorMessage
        );

        console.error(error);
    }
}


const messageInput =
    document.getElementById(
        "messageInput"
    );

if (messageInput) {

    messageInput.addEventListener(
        "keypress",
        (e) => {

            if (e.key === "Enter") {

                sendMessage();

            }

        }
    );

}