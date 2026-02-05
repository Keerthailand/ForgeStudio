document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chatWindow");
    const msgInput = document.getElementById("msgInput");
    const btnSend = document.getElementById("btnSend");
    const btnReset = document.getElementById("btnReset");
    const errorBar = document.getElementById("errorBar");
    const suggestionBox = document.getElementById("suggestionBox");
  
    // Seed message (client-side render)
    appendMessage({
      role: "bot",
      meta: "ForgeStudio • Anvil",
      text: "Welcome back to the anvil ⚒️\nTell me what you’re trying to create — and I’ll help you choose the smartest next move."
    });
  
    function showError(msg){
      errorBar.hidden = false;
      errorBar.textContent = msg;
    }
    function clearError(){
      errorBar.hidden = true;
      errorBar.textContent = "";
    }
  
    function appendMessage({ role, meta, text }) {
      const wrapper = document.createElement("div");
      wrapper.className = role === "user" ? "msg msg-user" : "msg msg-bot";
  
      const metaDiv = document.createElement("div");
      metaDiv.className = "msg-meta";
      metaDiv.textContent = meta;
  
      const bubble = document.createElement("div");
      bubble.className = "msg-bubble";
      bubble.textContent = text;
  
      wrapper.appendChild(metaDiv);
      wrapper.appendChild(bubble);
  
      chatWindow.appendChild(wrapper);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  
    function setSuggestion(text){
      if (!text){
        suggestionBox.hidden = true;
        suggestionBox.textContent = "";
        return;
      }
      suggestionBox.hidden = false;
      suggestionBox.textContent = text;
    }
  
    async function send(){
      clearError();
      const message = (msgInput.value || "").trim();
      if (!message){
        showError("Say something and I’ll help.");
        return;
      }
  
      btnSend.disabled = true;
      setSuggestion("");
  
      appendMessage({ role: "user", meta: "You", text: message });
      msgInput.value = "";
  
      // typing indicator
      const typing = document.createElement("div");
      typing.className = "msg msg-bot";
      typing.innerHTML = `
        <div class="msg-meta">ForgeStudio • Anvil</div>
        <div class="msg-bubble">Thinking… ⚒️</div>
      `;
      chatWindow.appendChild(typing);
      chatWindow.scrollTop = chatWindow.scrollHeight;
  
      try{
        const res = await fetch("/anvil/chat/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: JSON.stringify({ message })
        });
  
        const data = await res.json();
  
        // remove typing indicator
        if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
  
        if (!res.ok){
          showError(data?.error || "Try again.");
          btnSend.disabled = false;
          return;
        }
  
        appendMessage({
          role: "bot",
          meta: "ForgeStudio • Anvil",
          text: data.assistant_message
        });
  
        // subtle suggestion (optional)
        if (data.subtle_suggestion){
          setSuggestion(data.subtle_suggestion);
        }
  
        msgInput.focus();
  
      } catch(e){
        if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
        showError("Network error — try again.");
      } finally {
        btnSend.disabled = false;
      }
    }
  
    async function reset(){
      clearError();
      setSuggestion("");
      btnReset.disabled = true;
  
      try{
        await fetch("/anvil/reset/", {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") }
        });
      } catch(e){
        // ignore network reset failures
      } finally {
        chatWindow.innerHTML = "";
        appendMessage({
          role: "bot",
          meta: "ForgeStudio • Anvil",
          text: "Reset complete ⚒️\nTell me what you’re trying to create — and I’ll help you choose the smartest next move."
        });
        btnReset.disabled = false;
        msgInput.focus();
      }
    }
  
    // quick prompts
    document.querySelectorAll("[data-q]").forEach(btn => {
      btn.addEventListener("click", () => {
        msgInput.value = btn.getAttribute("data-q");
        msgInput.focus();
      });
    });
  
    btnSend.addEventListener("click", send);
    btnReset.addEventListener("click", reset);
  
    msgInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter"){
        e.preventDefault();
        send();
      }
    });
  
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(";").shift();
      return "";
    }
  });
  