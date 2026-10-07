/* Real clicks (element.click) on the page's own controls. Never fires the event under test by hand. */
(function(){
var R = [], errs = 0;
window.addEventListener("error", function(){ errs++; });
function q(s){ return document.querySelector(s); }
function qa(s){ return document.querySelectorAll(s); }
setTimeout(function(){
  try {
    var c = RECIPES.cards[0], card = function(){ return document.getElementById("c-" + c.id); };
    var first = function(){ return card().querySelector(".ing li .tx").textContent; };
    R.push("cards=" + qa(".card").length + "/" + RECIPES.cards.length);
    var before = first();
    var li = card().querySelector(".ing li"); li.click();
    R.push("ticked=" + li.classList.contains("tick"));
    var step = card().querySelector(".met li"); step.click();
    R.push("stepTicked=" + step.classList.contains("tick"));
    var sizes = card().querySelectorAll(".sizes button"), x2 = null;
    for (var i = 0; i < sizes.length; i++) if (/×2/.test(sizes[i].textContent)) x2 = sizes[i];
    if (x2) x2.click();
    var after = first(), want = c.groups[0].items[0].v[c.opts.map(function(o){return o.f;}).indexOf(2)].t;
    R.push("rescaled=" + (after === want && after !== before ? "ok" : JSON.stringify(before) + "->" + JSON.stringify(after)));
    R.push("chip=" + JSON.stringify((card().querySelector(".chip.scaled") || {}).textContent || "none"));
    R.push("tickSurvivesRescale=" + card().querySelector(".ing li").classList.contains("tick"));
    var on = card().querySelector(".sizes button.on"); R.push("pressed=" + (on && on.getAttribute("aria-pressed")));
    q('[data-pop="look"]').click(); q('[data-bg="night"]').click();
    R.push("bg=" + document.documentElement.getAttribute("data-bg"));
    q('[data-act="untick"]').click();
    R.push("cleared=" + (qa("li.tick").length === 0));
    var st = null; try { st = JSON.parse(localStorage.getItem("recipe-cards:" + RECIPES.id)); } catch(e){}
    R.push("savedSize=" + (st && st.size && st.size[c.id]));
    var howto = q(".howto"); R.push("howto=" + (howto ? JSON.stringify(howto.querySelector("b").textContent) : "none"));
    R.push("flag=" + qa(".flag").length);
  } catch(ex){ R.push("EXCEPTION " + ex.message); errs++; }
  document.body.setAttribute("data-r", "errors=" + errs + " | " + R.join(" | "));
}, 400);
})();
