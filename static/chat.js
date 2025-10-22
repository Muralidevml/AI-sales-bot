document.addEventListener("DOMContentLoaded", () => {
  const messagesDiv = document.getElementById("messages");
  const userInput = document.getElementById("userInput");
  const sendBtn = document.getElementById("sendBtn");

  function addMessage(content, sender) {
    const msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "user-msg" : "ai-msg";
    msgDiv.innerHTML = content;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    addMessage(`<b>You:</b> ${message}`, "user");
    userInput.value = "";

    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();
    let aiReply = data.reply.replace(/\n/g, "<br>"); // maintain line breaks

    // --- Format product results neatly ---
    if (data.products && data.products.length > 0) {
      aiReply += `<div class="mt-3"><b>✨ Matching Products:</b></div>`;
      aiReply += `<div class="row mt-2">`;

      data.products.forEach((p) => {
        aiReply += `
          <div class="col-12 mb-2">
            <div class="card p-2 shadow-sm">
              <div><b>${p.name}</b></div>
              <div style="font-size: 14px; color:#555;">${p.description}</div>
            </div>
          </div>`;
      });

      aiReply += `</div>`;
    }

    addMessage(`<b>Assistant:</b> ${aiReply}`, "ai");
  }

  sendBtn.addEventListener("click", sendMessage);
  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
});
