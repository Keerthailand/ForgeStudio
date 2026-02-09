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

  // Modal elements (must exist in improve.html)
  const imagePreviewModal = document.getElementById("imagePreviewModal");
  const previewImage = document.getElementById("previewImage");
  const closePreviewModalBtn = document.getElementById("closePreviewModal");

  let lastVariants = [];
  let isGenerating = false;

  // -----------------------------
  // Helpers
  // -----------------------------
  function showError(msg) {
    if (!errorBar) return;
    errorBar.hidden = false;
    errorBar.textContent = msg || "Something went wrong.";
  }

  function clearError() {
    if (!errorBar) return;
    errorBar.hidden = true;
    errorBar.textContent = "";
  }

  function escapeHtml(str) {
    return (str || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  async function copyToClipboard(text) {
    const t = text || "";
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(t);
      return;
    }
    const ta = document.createElement("textarea");
    ta.value = t;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }

  function downloadText(filename, text) {
    const blob = new Blob([text || ""], { type: "text/plain;charset=utf-8" });
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
    bubble.textContent = text || "";

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

  // -----------------------------
  // Modal
  // -----------------------------
  function openImagePreview(url) {
    if (!imagePreviewModal || !previewImage) return;

    if (!url) {
      showError("Image is still generating (or wasn’t returned). Try again in a moment.");
      return;
    }

    previewImage.src = url;
    imagePreviewModal.hidden = false;
    document.body.classList.add("no-scroll");
  }

  function closeImagePreview() {
    if (!imagePreviewModal || !previewImage) return;
    imagePreviewModal.hidden = true;
    previewImage.src = "";
    document.body.classList.remove("no-scroll");
  }

  closePreviewModalBtn?.addEventListener("click", closeImagePreview);

  imagePreviewModal?.addEventListener("click", (e) => {
    const t = e.target;
    if (t && t.dataset && t.dataset.close === "true") closeImagePreview();
  });

  document.addEventListener("keydown", (e) => {
    if (!imagePreviewModal || imagePreviewModal.hidden) return;
    if (e.key === "Escape") closeImagePreview();
  });

  // -----------------------------
  // File UI
  // -----------------------------
  fileInput?.addEventListener("change", () => {
    fileName.textContent = fileInput.files?.[0]?.name || "No file selected";
  });

  // -----------------------------
  // Side cards rendering
  // -----------------------------
  function renderSideCards(variants, generating = false) {
    sideCards.innerHTML = "";

    // If generating but no variants yet, show placeholders
    const baseVariants = variants && variants.length ? variants : [
      { label: "Version A", tone: "Bold + engaging", improved_text: "" },
      { label: "Version B", tone: "Clean + professional", improved_text: "" },
      { label: "Version C", tone: "Friendly + conversational", improved_text: "" },
    ];

    baseVariants.forEach((v, idx) => {
      const improved = v.improved_text || "";
      const previewText = improved
        ? (escapeHtml(improved).slice(0, 140) + (improved.length > 140 ? "…" : ""))
        : (generating ? `<span class="muted">Generating text…</span>` : "");

      let thumbHtml = "";
      if (generating) {
        thumbHtml = `
          <div class="side-thumb-loading" title="Generating image…">
            <span class="spinner"></span>
            <span>Generating…</span>
          </div>
        `;
      } else if (v.image_url) {
        thumbHtml = `
          <button class="side-thumb-btn" type="button" data-preview="${idx}" title="Preview image">
            <img class="side-thumb" src="${v.image_url}" alt="Preview" loading="lazy">
          </button>
        `;
      } else {
        thumbHtml = `<div class="side-thumb-missing" title="No image returned">No image</div>`;
      }

      const card = document.createElement("div");
      card.className = "side-card";

      card.innerHTML = `
        <div class="top">
          <div class="label">${escapeHtml(v.label || `Version ${idx + 1}`)}</div>
          <div class="tone">${escapeHtml(v.tone || "")}</div>
        </div>

        <div class="preview">${previewText}</div>

        <div class="side-thumb-row">${thumbHtml}</div>

        <div class="side-actions">
          <button class="small-btn" type="button" data-copy="${idx}" ${generating ? "disabled" : ""}>Copy</button>
          <button class="small-btn" type="button" data-open="${idx}" ${generating ? "disabled" : ""}>Open</button>
        </div>
      `;

      sideCards.appendChild(card);
    });
  }

  // Side cards delegation
  sideCards?.addEventListener("click", async (e) => {
    const t = e.target;

    // If generating, block interaction (buttons disabled anyway)
    if (isGenerating) return;

    const copyBtn = t.closest("[data-copy]");
    if (copyBtn) {
      const idx = parseInt(copyBtn.getAttribute("data-copy"), 10);
      const v = lastVariants[idx];
      if (!v) return;
      try {
        await copyToClipboard(v.improved_text || "");
        copyBtn.textContent = "Copied!";
        setTimeout(() => (copyBtn.textContent = "Copy"), 900);
      } catch {
        copyBtn.textContent = "Failed";
        setTimeout(() => (copyBtn.textContent = "Copy"), 900);
      }
      return;
    }

    const openBtn = t.closest("[data-open]");
    if (openBtn) {
      const idx = parseInt(openBtn.getAttribute("data-open"), 10);
      const v = lastVariants[idx];
      if (!v) return;
      openImagePreview(v.image_url || "");
      return;
    }

    const previewBtn = t.closest("[data-preview]");
    if (previewBtn) {
      const idx = parseInt(previewBtn.getAttribute("data-preview"), 10);
      const v = lastVariants[idx];
      if (!v) return;
      openImagePreview(v.image_url || "");
      return;
    }
  });

  // -----------------------------
  // Drawer
  // -----------------------------
  function openDrawer() {
    if (!lastVariants || lastVariants.length === 0) return;

    variantsList.innerHTML = "";
    lastVariants.forEach((v, idx) => {
      const card = document.createElement("div");
      card.className = "var-card";

      card.innerHTML = `
        <div class="var-top">
          <div class="var-label">${escapeHtml(v.label || `Version ${idx + 1}`)}</div>
          <div class="var-tone">${escapeHtml(v.tone || "")}</div>
        </div>

        <div class="var-body">${escapeHtml(v.improved_text || "")}</div>

        <div class="side-actions" style="margin-top:12px;">
          <button class="small-btn" type="button" data-copy-idx="${idx}">Copy</button>
          <button class="small-btn" type="button" data-dl-idx="${idx}">Download</button>
          <button class="small-btn" type="button" data-preview-idx="${idx}">Preview</button>
        </div>

        <div class="msg-image" style="margin-top:12px;">
          ${
            v.image_url
              ? `<img src="${v.image_url}" alt="Generated image" loading="lazy" style="cursor:pointer;" data-preview-idx="${idx}">`
              : `<div class="side-thumb-missing">No image returned</div>`
          }
        </div>

        <div style="margin-top:10px; color:#b7b7c2; font-weight:700; font-size:13px;">
          Image prompt: ${escapeHtml(v.image_prompt || "")}
        </div>
      `;

      variantsList.appendChild(card);
    });

    drawer.hidden = false;
  }

  function closeDrawer() {
    drawer.hidden = true;
  }

  variantsList?.addEventListener("click", async (e) => {
    const t = e.target;

    const copyBtn = t.closest("[data-copy-idx]");
    if (copyBtn) {
      const idx = parseInt(copyBtn.getAttribute("data-copy-idx"), 10);
      const v = lastVariants[idx];
      if (!v) return;

      try {
        await copyToClipboard(v.improved_text || "");
        copyBtn.textContent = "Copied!";
        setTimeout(() => (copyBtn.textContent = "Copy"), 900);
      } catch {
        copyBtn.textContent = "Failed";
        setTimeout(() => (copyBtn.textContent = "Copy"), 900);
      }
      return;
    }

    const dlBtn = t.closest("[data-dl-idx]");
    if (dlBtn) {
      const idx = parseInt(dlBtn.getAttribute("data-dl-idx"), 10);
      const v = lastVariants[idx];
      if (!v) return;

      const label = (v.label || `version_${idx + 1}`).replace(/\s+/g, "_").toLowerCase();
      downloadText(`forgestudio_improve_${label}.txt`, v.improved_text || "");
      return;
    }

    const prevBtn = t.closest("[data-preview-idx]");
    if (prevBtn) {
      const idx = parseInt(prevBtn.getAttribute("data-preview-idx"), 10);
      const v = lastVariants[idx];
      if (!v) return;

      openImagePreview(v.image_url || "");
      return;
    }
  });

  // -----------------------------
  // Improve action
  // -----------------------------
  async function improve() {
    clearError();

    const content = (contentInput.value || "").trim();
    const goal = (goalInput.value || "").trim();
    const file = fileInput.files?.[0] || null;

    if (!content && !file) {
      showError("Paste content or upload a file — then I can improve it 🔥");
      return;
    }

    isGenerating = true;
    btnImprove.disabled = true;
    btnShowVariants.disabled = true;

    // Render "generating" placeholders immediately
    renderSideCards([], true);

    appendMessage({
      role: "user",
      meta: "You",
      text: content ? content : `Uploaded file: ${file.name}`,
    });

    appendMessage({
      role: "bot",
      meta: "ForgeStudio • Improve",
      text: "Got it — I’m sharpening this now. One moment… 🔥",
    });

    try {
      const fd = new FormData();
      fd.append("content", content);
      fd.append("goal", goal);
      if (file) fd.append("file", file);

      const res = await fetch("/improve/analyze/", {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: fd,
      });

      const data = await res.json();

      // remove "one moment" message
      if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);

      if (!res.ok) {
        showError(data?.error || "Couldn’t improve that. Try again.");
        // Restore default side state
        renderSideCards([], false);
        return;
      }

      appendMessage({
        role: "bot",
        meta: "ForgeStudio • Improve",
        text: data.assistant_message || "Done 🔥",
      });

      lastVariants = Array.isArray(data.variants) ? data.variants : [];
      renderSideCards(lastVariants, false);

      btnShowVariants.disabled = lastVariants.length === 0;

      // Clear inputs
      contentInput.value = "";
      goalInput.value = "";
      fileInput.value = "";
      fileName.textContent = "No file selected";
    } catch (e) {
      if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
      showError("Network error — try again.");
      renderSideCards([], false);
    } finally {
      isGenerating = false;
      btnImprove.disabled = false;
    }
  }

  // -----------------------------
  // Button wiring
  // -----------------------------
  btnImprove?.addEventListener("click", improve);
  btnShowVariants?.addEventListener("click", openDrawer);
  btnCloseDrawer?.addEventListener("click", closeDrawer);

  // Initial side state
  renderSideCards([], false);
});
