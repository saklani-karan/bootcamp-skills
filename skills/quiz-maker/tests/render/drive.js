<script>
/* test driver: steps named in the hash, e.g. #play-front */
(function(){
  var step = location.hash.slice(1).split("-"), app = document.getElementById("app");
  function clk(sel){ var e = document.querySelector(sel); if(e) e.click(); return !!e; }
  try{ localStorage.clear(); }catch(e){}
  var look = step.indexOf("night")>=0 ? "night" : step.indexOf("sunset")>=0 ? "sunset" : null;
  function go(){
    clk('[data-act="addp"]'); var nm = document.getElementById("nm"); if(nm){ nm.value = "Leo"; clk('[data-act="savename"]'); }
    if(look){ clk('[data-go="menu"]'); clk('[data-bgc="'+look+'"]'); if(step.indexOf("hand")>=0) clk('[data-font="hand"]'); if(step.indexOf("photo")>=0) clk('[data-bgp="fortress"]'); clk('[data-go="home"]'); }
    if(step[0]==="home") return;
    if(step[0]==="seek"){ var all = document.querySelectorAll("[data-count]"); all[all.length-1].click(); clk('[data-act="start"]');
      var want = QUIZ.questions.filter(function(x){ return x.id === step[1]; })[0].q;
      for(var n=0;n<40;n++){ if(document.querySelector(".q").textContent === want) break; pickAnswer(true); clk('[data-act="next"]'); }
      if(step[2]==="back") pickAnswer(step[3]!=="wrong");
      if(step[2]==="enter"){ pickAnswer(true); document.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"})); }
      return; }
    if(step[0]==="menu"){ clk('[data-go="menu"]'); return; }
    clk('[data-act="start"]');
    if(step[1]==="front") return;
    if(step[1]==="hint"){ clk('[data-act="hint"]'); return; }
    if(step[1]==="wrong" || step[1]==="right"){ var c = document.querySelectorAll(".opt"); var want = step[1]==="right"; for(var i=0;i<c.length;i++){ var b=c[i]; } 
      // find right via data: compare with engine answer by trial on a clone is impossible; use QUIZ
      return pickAnswer(want); }
    if(step[1]==="end" || step[1]==="history" || step[1]==="answers"){
      for(var k=0;k<40;k++){ if(!document.querySelector(".opt")) break; pickAnswer(k%3!==0, true); clk('[data-act="next"]'); }
      if(step[1]==="history"){ clk('[data-act="again"]'); for(var k2=0;k2<40;k2++){ if(!document.querySelector(".opt")) break; pickAnswer(k2%2===0, true); clk('[data-act="next"]'); } clk('[data-go="history"]'); }
      if(step[1]==="answers") clk('[data-go="answers"]');
    }
  }
  window.pickAnswer = function(want, fast){
    var q = document.querySelector(".q").textContent, c = QUIZ.questions.filter(function(x){ return x.q === q; })[0];
    var opts = document.querySelectorAll(".opt"), target = null;
    for(var i=0;i<opts.length;i++){ var v = Number(opts[i].getAttribute("data-opt")); var isR = c.t==="tf" ? (v===1)===!!c.a : v===c.a; if(isR===want){ target = opts[i]; break; } }
    target.click();
    if(fast){ var k = document.getElementById("card"); }
  };
  setTimeout(go, 50);
})();
</script>
