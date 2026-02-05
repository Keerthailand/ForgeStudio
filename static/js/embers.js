(function(){
    const canvas = document.getElementById("ember-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
  
    let w, h, embers;
  
    function resize(){
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      embers = Array.from({length: Math.min(160, Math.floor(w / 8))}, spawn);
    }
  
    function spawn(){
      return {
        x: Math.random() * w,
        y: h + Math.random() * 120,
        r: Math.random() * 2.2 + 0.6,
        vy: Math.random() * 0.9 + 0.35,
        vx: (Math.random() - 0.5) * 0.25,
        a: Math.random() * 0.55 + 0.15
      };
    }
  
    function tick(){
      ctx.clearRect(0, 0, w, h);
      for (const e of embers){
        ctx.fillStyle = `rgba(255,106,0,${e.a})`;
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
        ctx.fill();
  
        e.y -= e.vy;
        e.x += e.vx;
  
        // slight drift
        e.vx += (Math.random() - 0.5) * 0.01;
  
        if (e.y < -10 || e.x < -20 || e.x > w + 20){
          Object.assign(e, spawn());
        }
      }
      requestAnimationFrame(tick);
    }
  
    window.addEventListener("resize", resize);
    resize();
    tick();
  })();
  