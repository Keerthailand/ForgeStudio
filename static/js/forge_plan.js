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
        key: "primary_goal",
        title: "What’s your primary goal?",
        options: [
          ["awareness", "Awareness", "More reach and visibility"],
          ["leads", "Leads", "DMs, clicks, signups"],
          ["trust", "Trust", "Authority and credibility"],
          ["sales", "Sales", "Conversion focus"],
        ]
      },
      {
        key: "funnel_stage",
        title: "Which stage are you focusing on?",
        options: [
          ["top", "Top of funnel", "Reach and discovery"],
          ["middle", "Middle", "Nurture and proof"],
          ["bottom", "Bottom", "Conversion and offers"],
        ]
      },
      {
        key: "seo_focus",
        title: "SEO direction?",
        options: [
          ["none", "None", "Pure clarity + shareability"],
          ["light", "Light", "1–2 phrases naturally"],
          ["strong", "Strong", "Consistent keyword themes"],
        ]
      },
      {
        key: "cadence",
        title: "Posting cadence you can sustain?",
        options: [
          ["low", "Low", "3 posts/week"],
          ["medium", "Medium", "5 posts/week"],
          ["high", "High", "7–10 posts/week"],
        ]
      },
      {
        key: "format_mix",
        title: "Content format mix?",
        options: [
          ["posts", "Posts", "Text/carousels only"],
          ["video", "Video", "Short/long video focus"],
          ["mixed", "Mixed", "Posts + videos"],
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
  
      if (idx < steps.length - 1){
        idx += 1;
        render();
        return;
      }
  
      progressFill.style.width = `100%`;
      questionText.textContent = "Building your plan…";
      optionsWrap.innerHTML = "";
  
      try{
        const res = await fetch("/forge/plan/evaluate/", {
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
      const plan = data.plan || {};
      const weekly = data.weekly_structure || [];
      const rules = data.operating_rules || [];
      const tools = data.next_tools || [];
  
      resultBox.classList.remove("muted");
      resultBox.textContent =
        `${data.headline}\n\n` +
        `Goal: ${plan.primary_goal}\n` +
        `Funnel stage: ${plan.funnel_stage}\n` +
        `Cadence: ${plan.cadence}\n` +
        `Format mix: ${plan.format_mix}\n` +
        `SEO direction: ${plan.seo_direction}\n\n` +
        `Weekly structure:\n- ${weekly.join("\n- ")}\n\n` +
        `Operating rules:\n- ${rules.join("\n- ")}\n`;
  
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
  
      questionText.textContent = "Plan Ready";
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
      resultBox.textContent = "Complete the flow to see a weekly structure.";
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
  