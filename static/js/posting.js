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
  const drawerInner = drawer?.querySelector(".drawer-inner") || null;

  let lastVariants = [];

  // ---- Hard reset on load (single source of truth = `hidden`)
  if (drawer) drawer.hidden = true;
  document.body.classList.remove("no-scroll");

  function showError(msg) {
    errorBar.hidden = false;
    errorBar.textContent = msg;
  }
  function clearError() {
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

  function setPreviews(platforms) {
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
    // clear immediately (you wanted this)
    promptInput.value = "";

    if (!prompt) {
      showError("Type a prompt first — give me something to forge 🔥");
      return;
    }

    btnGenerate.disabled = true;
    btnVariations.disabled = true;

    appendMessage({ role: "user", meta: "You", text: prompt });

    appendMessage({
      role: "bot",
      meta: "ForgeStudio • Posting",
      text: "Heating the metal… shaping the words… one moment 🔥",
    });

    try {
      const res = await fetch("/posting/generate/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();

      // Remove the “heating…” message
      if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);

      if (!res.ok) {
        showError(data?.error || "Couldn’t forge that. Try again.");
        return;
      }

      appendMessage({
        role: "bot",
        meta: "ForgeStudio • Posting",
        text: data.assistant_message,
        imageUrl: data.image?.url || null,
      });

      setPreviews(data.platforms);

      lastVariants = Array.isArray(data.variants) ? data.variants : [];
      btnVariations.disabled = lastVariants.length === 0;

      promptInput.focus();
    } catch (e) {
      if (chatWindow.lastElementChild) chatWindow.removeChild(chatWindow.lastElementChild);
      showError("Network error. Your forge flames flickered — try again.");
    } finally {
      btnGenerate.disabled = false;
    }
  }

  // ---- Drawer controls (single mechanism: hidden)
  function openVariations() {
    clearError();

    if (!drawer || !variationsList) {
      showError("Variations UI missing. Check #variationsDrawer and #variationsList in posting.html.");
      return;
    }
    if (!lastVariants || lastVariants.length === 0) return;

    variationsList.innerHTML = "";

    lastVariants.forEach((v) => {
      const card = document.createElement("div");
      card.className = "var-card";

      // escape (basic)
      const label = String(v.label || "");
      const tone = String(v.tone || "");
      const ig = String(v.instagram || "");
      const x = String(v.x || "");
      const fb = String(v.facebook || "");
      const li = String(v.linkedin || "");

      card.innerHTML = `
        <div class="var-top">
          <div class="var-label">${escapeHtml(label)}</div>
          <div class="var-tone">${escapeHtml(tone)}</div>
        </div>
        <div class="var-body">
          <strong>Instagram</strong><br>${escapeHtml(ig).replaceAll("\n", "<br>")}
          <br><br>
          <strong>X</strong><br>${escapeHtml(x).replaceAll("\n", "<br>")}
          <br><br>
          <strong>Facebook</strong><br>${escapeHtml(fb).replaceAll("\n", "<br>")}
          <br><br>
          <strong>LinkedIn</strong><br>${escapeHtml(li).replaceAll("\n", "<br>")}
        </div>
      `;

      variationsList.appendChild(card);
    });

    drawer.hidden = false;
    document.body.classList.add("no-scroll");
  }

  function closeVariations() {
    if (!drawer) return;
    drawer.hidden = true;
    document.body.classList.remove("no-scroll");
  }

  // Buttons
  btnGenerate?.addEventListener("click", generate);
  btnVariations?.addEventListener("click", openVariations);
  btnCloseDrawer?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    closeVariations();
  });

  // Click overlay closes (anything with data-close="true")
  drawer?.addEventListener("click", (e) => {
    const t = e.target;
    if (t?.dataset?.close === "true") closeVariations();
  });

  // Prevent inner clicks from bubbling to overlay
  drawerInner?.addEventListener("click", (e) => e.stopPropagation());

  // Escape closes only if open
  document.addEventListener("keydown", (e) => {
    if (!drawer || drawer.hidden) return;
    if (e.key === "Escape") closeVariations();
  });

  // Enter to send
  promptInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      generate();
    }
  });

  // ---- Helpers
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  function escapeHtml(str) {
    return (str || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }
});
