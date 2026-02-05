document.addEventListener("DOMContentLoaded", () => {
    const questionText = document.getElementById("questionText");
    const optionsWrap = document.getElementById("optionsWrap");
    const stepLabel = document.getElementById("stepLabel");
    const progressFill = document.getElementById("progressFill");
    const resultBox = document.getElementById("resultBox");
    const btnBack = document.getElementById("btnBack");
    const btnRestart = document.getElementById("btnRestart");
    const errorBar = document.getElementById("errorBar");
  
    const steps = [
      {
        key: "goal",
        title: "What’s your primary goal?",
        options: [
          ["awareness", "Awareness", "More reach and visibility"],
          ["leads", "Leads", "Get people to DM/click/signup"],
          ["trust", "Trust", "Build credibility and authority"],
          ["sales", "Sales", "Move toward conversions"],
        ]
      },
      {
        key: "audience_temp",
        title: "How warm is your audience?",
        options: [
          ["cold", "Cold", "They don’t know you yet"],
          ["warm", "Warm", "They’ve seen you a few times"],
          ["hot", "Hot", "They’re ready to act"],
        ]
      },
      {
        key: "style",
        title: "What style fits best today?",
        options: [
          ["educational", "Educational", "Teach something useful"],
          ["entertaining", "Entertaining", "Fast, fun, high retention"],
          ["story", "Story", "Personal lesson + insight"],
          ["opinion", "Opinion", "A strong take with reasoning"],
        ]
      },
      {
        key: "tone",
        title: "Pick a tone:",
        options: [
          ["bold", "Bold", "Confident, punchy"],
          ["clean", "Clean", "Minimal, professional"],
          ["friendly", "Friendly", "Warm, conversational"],
        ]
      },
      {
        key: "platform",
        title: "Where are you posting?",
        options: [
          ["instagram", "Instagram", "Visual + captions"],
          ["tiktok", "TikTok", "Short-form video"],
          ["x", "X", "Punchy thoughts"],
          ["facebook", "Facebook", "Conversational"],
          ["linkedin", "LinkedIn", "Professional value"],
        ]
      }
    ];
  
    let idx = 0;
    const answers = {};
  
    function setError(msg){
      errorBar.hidden = !msg;
      errorBar.textContent = msg || "";
    }
  
    function render(){
      setError("");
      const step = steps[idx];
      stepLabel.textContent = `Step ${idx + 1} of ${steps.length}`;
      progressFill.style.width = `${Math.round((idx / steps.length) * 100)}%`;
      questionText.textContent = step.title;
  
      optionsWrap.innerHTML = "";
      step.options.forEach(([val, title, sub]) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "option-btn";
        btn.innerHTML = `${title}<span class="option-sub">${sub}</span>`;
        btn.addEventListener("click", () => choose(step.key, val));
        optionsWrap.appendChild(btn);
      });
  
      btnBack.disabled = idx === 0;
    }
  
    async function choose(key, val){
      answers[key] = val;
  
      // next
      if (idx < steps.length - 1){
        idx += 1;
        render();
        return;
      }
  
      // finished
      progressFill.style.width = `100%`;
      questionText.textContent = "Forging recommendations…";
      optionsWrap.innerHTML = "";
  
      try{
        const res = await fetch("/forge/brainstorm/evaluate/", {
          method: "POST",
          headers: {
            "Content-Type":"application/json",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: JSON.stringify({ answers })
        });
        const data = await res.json();
  
        if (!res.ok){
          setError(data?.error || "Couldn’t evaluate. Try again.");
          render();
          return;
        }
  
        showResults(data);
  
      } catch(e){
        setError("Network error. Try again.");
        render();
      }
    }
  
    function showResults(data){
      const r = data.recommendations || {};
      const tips = data.tips || [];
      const tools = data.next_tools || [];
  
      resultBox.classList.remove("muted");
      resultBox.textContent =
        `${data.headline}\n\n` +
        `Best content type: ${r.best_content_type}\n` +
        `Best platform: ${r.best_platform}\n` +
        `Best tone: ${r.best_tone}\n` +
        `Audience: ${r.audience_temperature}\n\n` +
        `Tips:\n- ${tips.join("\n- ")}\n`;
  
      // tool pills
      const pills = document.createElement("div");
      pills.className = "result-tools";
  
      tools.forEach(t => {
        const a = document.createElement("a");
        a.className = "tool-pill";
        a.href = toolHref(t.tool);
        a.textContent = `${t.tool}`;
        a.title = t.why || "";
        pills.appendChild(a);
      });
  
      resultBox.appendChild(pills);
  
      // lock UI
      questionText.textContent = "Results Ready";
      optionsWrap.innerHTML = "";
    }
  
    function toolHref(tool){
      const t = (tool || "").toLowerCase();
      if (t.includes("posting")) return "/posting/";
      if (t.includes("improve")) return "/improve/";
      if (t.includes("script")) return "/script/";
      if (t.includes("forge")) return "/forge/";
      return "/posting/";
    }
  
    btnBack.addEventListener("click", () => {
      if (idx === 0) return;
      idx -= 1;
      render();
    });
  
    btnRestart.addEventListener("click", () => {
      idx = 0;
      for (const k in answers) delete answers[k];
      resultBox.textContent = "Complete the flow to see recommendations.";
      resultBox.classList.add("muted");
      render();
    });
  
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(";").shift();
      return "";
    }
  
    render();
  });
  