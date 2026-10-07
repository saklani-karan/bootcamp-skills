/* Real clicks only (element.click). Never fires the event under test by hand. */
(function(){
var R = [], errs = 0;
window.addEventListener("error", function(){ errs++; });
window.print = function(){ R.push("printed:" + document.body.className); };   // the print dialog is not under test
function q(s){ return document.querySelector(s); }
function qa(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); }
setTimeout(function(){
  try {
    var S = window.__event.state();
    q('[data-tab="shop"]').click();
    R.push("shopVisible=" + (getComputedStyle(q("#shop")).display !== "none") + "/guestHidden=" + (getComputedStyle(q("#guest")).display === "none"));
    var first = EVENT.stores[0].name;
    q('[data-store="' + first + '"]').click();
    var shown = qa(".line").length, expect = EVENT.lines.filter(function(l){ return l.store === first; }).length;
    R.push("filter=" + (shown === expect ? "ok" : shown + "!=" + expect));
    var ids = qa(".line").slice(0, 2).map(function(el){ return el.getAttribute("data-line"); });
    ids.forEach(function(id){ q('[data-tick="' + id + '"]').click(); });
    var want = EVENT.lines.filter(function(l){ return ids.indexOf(l.id) >= 0; }).reduce(function(s, l){ return s + Math.round(parseFloat(l.cost) * 100); }, 0);
    var storeTotal = EVENT.lines.filter(function(l){ return l.store === first; }).reduce(function(s, l){ return s + Math.round(parseFloat(l.cost) * 100); }, 0);
    var run = q("#running").textContent.replace(/,/g, "");
    var ok = run.indexOf("2 of " + expect) >= 0 && run.indexOf("$" + (want / 100).toFixed(2) + " of $" + (storeTotal / 100).toFixed(2)) >= 0;
    R.push("running=" + (ok ? "ok" : JSON.stringify(run)));
    q('[data-tick="' + ids[0] + '"]').click();
    R.push("untick=" + (q('[data-line="' + ids[0] + '"]').classList.contains("done") ? "stuck" : "ok"));
    q('[data-store=""]').click();
    R.push("allStores=" + (qa(".line").length === EVENT.lines.length));
    var saved = null; try { saved = JSON.parse(localStorage.getItem("event:" + EVENT.id)); } catch(x){}
    R.push("saved=" + (saved && saved.ticks[ids[1]] && !saved.ticks[ids[0]] ? "ok" : "no"));
    ["guest", "plan", "money", "questions"].forEach(function(t){ q('[data-tab="' + t + '"]').click(); if (getComputedStyle(q("#" + t)).display === "none") R.push("tab " + t + " hidden"); });
    R.push("tabs=ok");
    q('#money [data-print="money"]').click();
    q('[data-pop="look"]').click(); q('[data-bg="night"]').click();
    R.push("bg=" + document.documentElement.getAttribute("data-bg"));
    R.push("splitRows=" + qa("#money tr").length);
  } catch(ex){ R.push("EXCEPTION " + ex.message); errs++; }
  document.body.setAttribute("data-r", "errors=" + errs + " | " + R.join(" | "));
}, 400);
})();
