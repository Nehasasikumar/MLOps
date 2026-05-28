// LOGIN

const loginBtn = document.getElementById("loginBtn");

if(loginBtn){

    loginBtn.addEventListener("click", () => {

        window.location.href = "../chatbot.html";

    });

}

// SIGNUP

const signupBtn = document.getElementById("signupBtn");

if(signupBtn){

    signupBtn.addEventListener("click", () => {

        window.location.href = "../chatbot.html";

    });

}

// CHATBOT

const sendBtn = document.querySelector(".send-btn");

if(sendBtn){

    sendBtn.addEventListener("click", sendMessage);

}

function sendMessage(){

    const input = document.getElementById("messageInput");

    const chatArea = document.getElementById("chatArea");

    const text = input.value.trim();

    if(text === "") return;

    // USER MESSAGE

    const userMessage = document.createElement("div");

    userMessage.classList.add("message","user");

    userMessage.innerText = text;

    chatArea.appendChild(userMessage);

    input.value = "";

    // BOT MESSAGE

    setTimeout(() => {

        const botMessage = document.createElement("div");

        botMessage.classList.add("message","bot");

        botMessage.innerText =
        "Analyzing source and generating semantic insights...";

        chatArea.appendChild(botMessage);

        chatArea.scrollTop = chatArea.scrollHeight;

    },1000);

}

// ENTER KEY

const messageInput = document.getElementById("messageInput");

if(messageInput){

    messageInput.addEventListener("keypress",(e)=>{

        if(e.key === "Enter"){

            sendMessage();

        }

    });

}