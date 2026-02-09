document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chatWindow");
    const promptInput = document.getElementById("promptInput");
    const btnGenerate = document.getElementById("btnGenerate");
    const btnVariations = document.getElementById("btnVariations");
    const errorBar = document.getElementById("errorBar");
  
    const previewInstagram = document.getElementById("previewInstagram");
    const previewX = document.getElementById("previewX");
    const previewFacebook = document.getElementById("previewFacebook");
    const previewLinkedIn = document.getElementById("previewLinkedIn");
  
    const drawer = document.getElementById("variationsDrawer");
    const btnCloseDrawer = document.getElementById("btnCloseDrawer");
    const variationsList = document.getElementById("variationsList");
  
    let lastVariants = null;

    // Hard reset on load so it can’t get stuck open
    if (drawer) drawer.hidden = true;
    if (drawer) drawer.classList.remove("is-open");


    function showError(msg){
      errorBar.hidden = false;
      errorBar.textContent = msg;
    }
    function clearError(){
      errorBar.hidden = true;
      errorBar.textContent = "";
    }
  
    function appendMessage({ role, meta, text, imageUrl }) {
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
  
      if (imageUrl) {
        const imgWrap = document.createElement("div");
        imgWrap.className = "msg-image";
        const img = document.createElement("img");
        img.src = imageUrl;
        img.alt = "Generated image";
        img.loading = "lazy";
        imgWrap.appendChild(img);
        wrapper.appendChild(imgWrap);
      }
  
      chatWindow.appendChild(wrapper);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  
    function setPreviews(platforms){
      previewInstagram.classList.remove("muted");
      previewX.classList.remove("muted");
      previewFacebook.classList.remove("muted");
      previewLinkedIn.classList.remove("muted");
  
      previewInstagram.textContent = platforms.instagram;
      previewX.textContent = platforms.x;
      previewFacebook.textContent = platforms.facebook;
      previewLinkedIn.textContent = platforms.linkedin;
    }
  
    async function generate() {
      clearError();
      const prompt = (promptInput.value || "").trim();
      promptInput.value = "";
      if (!prompt) {
        showError("Type a prompt first — give me something to forge 🔥");
        return;
      }
  
      btnGenerate.disabled = true;
      btnVariations.disabled = true;
  
      appendMessage({
        role: "user",
        meta: "You",
        text: prompt
      });
  
      appendMessage({
        role: "bot",
        meta: "ForgeStudio • Posting",
        text: "Heating the metal… shaping the words… one moment 🔥"
      });
  
      try {
        const res = await fetch("/posting/generate/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: JSON.stringify({ prompt })
        });
  
        const data = await res.json();
  
        // Remove the “heating…” message (last bot message)
        // Safe approach: remove last child only if it exists
        if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
  
        if (!res.ok) {
          showError(data?.error || "Couldn’t forge that. Try again.");
          btnGenerate.disabled = false;
          return;
        }
  
        appendMessage({
          role: "bot",
          meta: "ForgeStudio • Posting",
          text: data.assistant_message,
          imageUrl: data.image?.url || null
        });
  
        setPreviews(data.platforms);
        lastVariants = data.variants || [];
        btnVariations.disabled = lastVariants.length === 0;
  
        promptInput.value = "";
        promptInput.focus();
  
      } catch (e) {
        // Remove the “heating…” message if still there
        if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
        showError("Network error. Your forge flames flickered — try again.");
      } finally {
        btnGenerate.disabled = false;
      }
    }
  
    function openVariations() {
      if (!drawer || !variationsList) {
        showError("Variations UI missing. Check #variationsDrawer and #variationsList in posting.html.");
        return;
      }
      if (!lastVariants || lastVariants.length === 0) return;
    
      variationsList.innerHTML = "";
    
      lastVariants.forEach(v => {
        const card = document.createElement("div");
        card.className = "var-card";
    
        card.innerHTML = `
          <div class="var-top">
            <div class="var-label">${v.label}</div>
            <div class="var-tone">${v.tone}</div>
          </div>
          <div class="var-body">Instagram:\n${v.instagram}\n\nX:\n${v.x}</div>
        `;
    
        variationsList.appendChild(card);
      });
    
      drawer.classList.add("is-open");
      document.body.classList.add("no-scroll");
    }
    
    function closeVariations() {
      if (!drawer) return;
      drawer.classList.remove("is-open");
      document.body.classList.remove("no-scroll");
    }
    
    
  
    btnGenerate.addEventListener("click", generate);
    btnVariations.addEventListener("click", openVariations);
    if (btnCloseDrawer) btnCloseDrawer.addEventListener("click", closeVariations);

  
    promptInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        generate();
      }
    });
  
    // Click outside the drawer-inner closes the modal
    if (drawer) {
      drawer.addEventListener("click", (e) => {
        if (e.target === drawer) closeVariations();
      });
    }

    // Escape key closes
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeVariations();
    });


    // Helper
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(";").shift();
      return "";
    }
  });
  