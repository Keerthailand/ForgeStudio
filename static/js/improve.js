document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chatWindow");
    const contentInput = document.getElementById("contentInput");
    const goalInput = document.getElementById("goalInput");
    const fileInput = document.getElementById("fileInput");
    const fileName = document.getElementById("fileName");
  
    const btnImprove = document.getElementById("btnImprove");
    const btnShowVariants = document.getElementById("btnShowVariants");
    const errorBar = document.getElementById("errorBar");
  
    const sideCards = document.getElementById("sideCards");
  
    const drawer = document.getElementById("variantsDrawer");
    const btnCloseDrawer = document.getElementById("btnCloseDrawer");
    const variantsList = document.getElementById("variantsList");
  
    let lastVariants = null;
  
    fileInput.addEventListener("change", () => {
      fileName.textContent = fileInput.files?.[0]?.name || "No file selected";
    });
  
    function showError(msg){
      errorBar.hidden = false;
      errorBar.textContent = msg;
    }
    function clearError(){
      errorBar.hidden = true;
      errorBar.textContent = "";
    }
    
    async function copyToClipboard(text) {
      // Modern
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return;
      }
    
      // Fallback (works on http://localhost too)
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    
    function downloadText(filename, text) {
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
    
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    
      URL.revokeObjectURL(url);
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
  
    async function improve(){
      clearError();
  
      const content = (contentInput.value || "").trim();
      const goal = (goalInput.value || "").trim();
      const file = fileInput.files?.[0] || null;
  
      if (!content && !file){
        showError("Paste content or upload a file — then I can improve it 🔥");
        return;
      }
  
      btnImprove.disabled = true;
      btnShowVariants.disabled = true;
  
      appendMessage({
        role: "user",
        meta: "You",
        text: content ? content : `Uploaded file: ${file.name}`
      });
  
      appendMessage({
        role: "bot",
        meta: "ForgeStudio • Improve",
        text: "Got it — I’m sharpening this now. One moment… 🔥"
      });
  
      try{
        const fd = new FormData();
        fd.append("content", content);
        fd.append("goal", goal);
        if (file) fd.append("file", file);
  
        const res = await fetch("/improve/analyze/", {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
          body: fd
        });
  
        const data = await res.json();
  
        // remove "one moment" message
        if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
  
        if (!res.ok){
          showError(data?.error || "Couldn’t improve that. Try again.");
          btnImprove.disabled = false;
          return;
        }
  
        appendMessage({
          role: "bot",
          meta: "ForgeStudio • Improve",
          text: data.assistant_message
        });
  
        lastVariants = data.variants || [];
        renderSideCards(lastVariants);
        btnShowVariants.disabled = lastVariants.length === 0;
  
        contentInput.value = "";
        goalInput.value = "";
        fileInput.value = "";
        fileName.textContent = "No file selected";
  
      } catch(e){
        if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
        showError("Network error — try again.");
      } finally {
        btnImprove.disabled = false;
      }
    }
  
    function renderSideCards(variants){
      sideCards.innerHTML = "";
      if (!variants || variants.length === 0){
        sideCards.innerHTML = `<div class="side-card muted">No variants returned.</div>`;
        return;
      }
  
      variants.forEach((v, idx) => {
        const card = document.createElement("div");
        card.className = "side-card";
  
        card.innerHTML = `
          <div class="top">
            <div class="label">${v.label}</div>
            <div class="tone">${v.tone}</div>
          </div>
          <div class="preview">${escapeHtml(v.improved_text).slice(0, 180)}${v.improved_text.length > 180 ? "…" : ""}</div>
          <div class="side-actions">
            <button class="small-btn" data-copy="${idx}">Copy</button>
            <button class="small-btn" data-open="${idx}">Open</button>
          </div>
        `;
  
        sideCards.appendChild(card);
      });
  
      sideCards.querySelectorAll("[data-copy]").forEach(btn => {
        btn.addEventListener("click", () => {
          const v = variants[parseInt(btn.getAttribute("data-copy"), 10)];
          navigator.clipboard.writeText(v.improved_text);
          btn.textContent = "Copied!";
          setTimeout(() => btn.textContent = "Copy", 900);
        });
      });
  
      sideCards.querySelectorAll("[data-open]").forEach(btn => {
        btn.addEventListener("click", () => {
          openDrawer();
        });
      });
    }
  
    function openDrawer(){
      if (!lastVariants || lastVariants.length === 0) return;
      variantsList.innerHTML = "";
  
      lastVariants.forEach(v => {
        const card = document.createElement("div");
        card.className = "var-card";
        card.innerHTML = `
          <div class="var-top">
            <div class="var-label">${v.label}</div>
            <div class="var-tone">${v.tone}</div>
          </div>

          <div class="var-body">${escapeHtml(v.improved_text)}</div>

          <div class="side-actions" style="margin-top:12px;">
            <button class="small-btn" data-copy="${v.label}">Copy</button>
            <button class="small-btn" data-dl="${v.label}">Download</button>
          </div>

          <div class="msg-image" style="margin-top:12px;">
            <img src="${v.image_url}" alt="Generated image" loading="lazy" />
          </div>

          <div style="margin-top:10px; color:#b7b7c2; font-weight:700; font-size:13px;">
            Image prompt: ${escapeHtml(v.image_prompt)}
          </div>
        `;
        variantsList.querySelectorAll("[data-copy]").forEach(btn => {
          btn.addEventListener("click", async () => {
            const label = btn.getAttribute("data-copy");
            const v = lastVariants.find(x => x.label === label);
            if (!v) return;
        
            try {
              await copyToClipboard(v.improved_text);
              btn.textContent = "Copied!";
              setTimeout(() => btn.textContent = "Copy", 900);
            } catch {
              btn.textContent = "Failed";
              setTimeout(() => btn.textContent = "Copy", 900);
            }
          });
        });
        
        variantsList.querySelectorAll("[data-dl]").forEach(btn => {
          btn.addEventListener("click", () => {
            const label = btn.getAttribute("data-dl");
            const v = lastVariants.find(x => x.label === label);
            if (!v) return;
        
            const safe = label.replace(/\s+/g, "_").toLowerCase();
            downloadText(`forgestudio_improve_${safe}.txt`, v.improved_text);
          });
        });
        
        variantsList.appendChild(card);
      });
  
      drawer.hidden = false;
    }
  
    function closeDrawer(){
      drawer.hidden = true;
    }
  
    btnImprove.addEventListener("click", improve);
    btnShowVariants.addEventListener("click", openDrawer);
    btnCloseDrawer.addEventListener("click", closeDrawer);
  
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(";").shift();
      return "";
    }
  
    function escapeHtml(str){
      return (str || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }
  });
  