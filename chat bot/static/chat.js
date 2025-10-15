document.getElementById("sendBtn").addEventListener("click", sendMessage);
document.getElementById("userInput").addEventListener("keypress", function(e) {
  if (e.key === "Enter") sendMessage();
});

async function sendMessage() {
  const input = document.getElementById("userInput");
  const msg = input.value.trim();
  if (!msg) return;

  const messagesDiv = document.getElementById("messages");
  messagesDiv.innerHTML += `<div class='user-msg'><b>You:</b> ${msg}</div>`;
  input.value = "";

  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: msg })
  });

  const data = await response.json();
  messagesDiv.innerHTML += `<div class='ai-msg'><b>AI:</b> ${data.reply}</div>`;
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
