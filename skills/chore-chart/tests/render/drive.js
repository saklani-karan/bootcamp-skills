/* Real clicks only (element.click). Never fires the event under test by hand. */
(function(){
var R = [], errs = 0;
window.addEventListener("error", function(){ errs++; });
window.print = function(){ R.push("printed:" + document.body.className.replace(/\s+/g, ".")); };   // the print dialog is not under test
function q(s){ return document.querySelector(s); }
function qa(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); }
function shown(id){ return getComputedStyle(document.getElementById(id)).display !== "none"; }
setTimeout(function(){
  try {
    var C = CHART, W = C.weeks.length, last = "w" + W;
    // tabs
    q('[data-tab="' + last + '"]').click();
    R.push("tab=" + (shown(last) && (W === 1 || !shown("w1")) ? "ok" : "no"));
    // every assignment on the page obeys the rules the build promised
    var bad = 0;
    C.weeks.forEach(function(w, wi){ w.owner.forEach(function(c, k){
      if (C.children[c].age < C.chores[k].min_age) bad++;
      if (wi && C.weeks[wi - 1].owner[k] === c && !C.chores[k].same) bad++; }); });
    R.push("rules=" + (bad ? bad + " broken" : "ok"));
    // the grid shows exactly the chores each child owns that week
    var wk = C.weeks[W - 1], items = qa("#" + last + " .item").length;
    R.push("cells=" + (items === wk.ticks ? "ok" : items + "!=" + wk.ticks));
    // tick two, untick one, persistence and the progress line
    var its = qa("#" + last + " .item"), id0 = its[0].getAttribute("data-tick"), id1 = its[its.length - 1].getAttribute("data-tick");
    its[0].click(); q('#' + last + ' [data-tick="' + id1 + '"]').click();
    var p = q("#" + last + " .progress").textContent;
    R.push("progress=" + (p.indexOf("2 of " + wk.ticks) === 0 ? "ok" : JSON.stringify(p)));
    var b0 = q('#' + last + ' [data-tick="' + id0 + '"]');
    R.push("ticked=" + (b0.classList.contains("done") && b0.getAttribute("aria-pressed") === "true" ? "ok" : "no"));
    b0.click();
    R.push("untick=" + (q('#' + last + ' [data-tick="' + id0 + '"]').classList.contains("done") ? "stuck" : "ok"));
    var saved = null; try { saved = JSON.parse(localStorage.getItem("chores:" + C.id)); } catch(x){}
    R.push("saved=" + (saved && saved.ticks[id1] && !saved.ticks[id0] ? "ok" : "no"));
    // the other weeks are untouched by a tick here
    R.push("isolated=" + (W === 1 || q("#w1 .progress").textContent.indexOf("0 of") === 0 ? "ok" : "no"));
    // rotation tab
    q('[data-tab="rota"]').click();
    R.push("rota=" + (shown("rota") && qa("#rota tr[data-chore]").length === C.chores.length ? "ok" : "no"));
    // look menu, then a tap on <html> itself (it carries data-bg/data-font) must change nothing and close the menu
    q('[data-pop="look"]').click(); q('[data-bg="night"]').click();
    var bg1 = root().getAttribute("data-bg"), f1 = root().getAttribute("data-font");
    root().click();
    var closed = !q("#pop-look").classList.contains("open");
    R.push("bg=" + bg1 + " htmlTap=" + (root().getAttribute("data-bg") === bg1 && root().getAttribute("data-font") === f1 && closed ? "ok" : "changed"));
    q('[data-pop="look"]').click(); q('[data-font="clear"]').click();
    R.push("font=" + root().getAttribute("data-font"));
    // print buttons set the right mode
    q('[data-tab="w1"]').click(); q('#w1 [data-print="all"]').click(); q('#w1 [data-print="week"]').click();
  } catch(ex){ R.push("EXCEPTION " + ex.message); errs++; }
  function root(){ return document.documentElement; }
  document.body.setAttribute("data-r", "errors=" + errs + " | " + R.join(" | "));
}, 400);
})();
