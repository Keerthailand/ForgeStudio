document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chatWindow");
    const topicInput = document.getElementById("topicInput");
    const lengthSelect = document.getElementById("lengthSelect");
    const platformSelect = document.getElementById("platformSelect");
  
    const btnGenerate = document.getElementById("btnGenerate");
    const btnDownload = document.getElementById("btnDownload");
  
    const scriptOutput = document.getElementById("scriptOutput");
  
    const loaderWrap = document.getElementById("loaderWrap");
    const loaderFill = document.getElementById("loaderFill");
  
    const errorBar = document.getElementById("errorBar");
  
    let loadingTimer = null;
  
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
  
    function startLoader(){
      loaderWrap.hidden = false;
      loaderFill.style.width = "0%";
      let p = 0;
  
      // Smooth fake progress up to 92% while waiting for server
      loadingTimer = setInterval(() => {
        p += Math.random() * 6;
        if (p > 92) p = 92;
        loaderFill.style.width = `${p}%`;
      }, 220);
    }
  
    function finishLoader(){
      if (loadingTimer) clearInterval(loadingTimer);
      loadingTimer = null;
      loaderFill.style.width = "100%";
      setTimeout(() => {
        loaderWrap.hidden = true;
        loaderFill.style.width = "0%";
      }, 400);
    }
  
    async function generate(){
      clearError();
      const topic = (topicInput.value || "").trim();
      if (!topic){
        showError("Type a topic first — what’s the script about?");
        return;
      }
  
      btnGenerate.disabled = true;
      btnDownload.setAttribute("aria-disabled", "true");
      btnDownload.classList.add("disabled");
      scriptOutput.textContent = "Forging script…";
      scriptOutput.classList.remove("muted");
  
      appendMessage({ role: "user", meta: "You", text: topic });
      appendMessage({ role: "bot", meta: "ForgeStudio • VideoScript", text: "Got it 🔥 forging your script now…" });
  
      startLoader();
  
      try{
        const res = await fetch("/script/generate/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: JSON.stringify({
            topic,
            length: lengthSelect.value,
            platform: platformSelect.value
          })
        });
  
        const data = await res.json();
        finishLoader();
  
        // remove last "forging..." bot message
        if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
  
        if (!res.ok){
          showError(data?.error || "Couldn’t generate that. Try again.");
          btnGenerate.disabled = false;
          scriptOutput.textContent = "Generate to see your script here.";
          scriptOutput.classList.add("muted");
          return;
        }
  
        appendMessage({ role: "bot", meta: "ForgeStudio • VideoScript", text: data.assistant_message });
  
        scriptOutput.textContent = data.script;
        scriptOutput.classList.remove("muted");
  
        // Enable download
        btnDownload.removeAttribute("aria-disabled");
        btnDownload.classList.remove("disabled");
  
        topicInput.value = "";
        topicInput.focus();
  
      } catch(e){
        finishLoader();
        if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
        showError("Network error — try again.");
        btnGenerate.disabled = false;
        scriptOutput.textContent = "Generate to see your script here.";
        scriptOutput.classList.add("muted");
      } finally {
        btnGenerate.disabled = false;
      }
    }
  
    btnGenerate.addEventListener("click", generate);
  
    // Enter to generate
    topicInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter"){
        e.preventDefault();
        generate();
      }
    });
  
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(";").shift();
      return "";
    }
  });
  