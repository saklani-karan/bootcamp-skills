/* Real clicks only (element.click). Never fires the event under test by hand.
   The download itself is not under test (headless has no Downloads folder): the anchor's click is
   recorded instead of followed, and the Blob the page made is read back byte for byte. */
(function(){
var R = [], errs = 0, blob = null, dl = null;
window.addEventListener("error", function(){ errs++; });
window.print = function(){ R.push("printed"); };
var mk = URL.createObjectURL; URL.createObjectURL = function(b){ blob = b; return mk.call(URL, b); };
HTMLAnchorElement.prototype.click = function(){ dl = this.getAttribute("download") + "|" + (this.href.indexOf("blob:") === 0 ? "blob" : this.href); };
function q(s){ return document.querySelector(s); }
function qa(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); }
function finish(){ document.body.setAttribute("data-r", "errors=" + errs + " | " + R.join(" | ")); }
setTimeout(function(){
  try {
    var S = window.__home.state(), rows = qa(".job");
    var want = HOME.months.reduce(function(s, m){ return s + m.items.length; }, 0);
    R.push("rows=" + (rows.length === want && want === HOME.facts.dates ? "ok" : rows.length + "!=" + want));
    var id0 = rows[0].getAttribute("data-job"), id1 = rows[1].getAttribute("data-job");
    q('[data-tick="' + id0 + '"]').click();
    var on = q('[data-job="' + id0 + '"]').classList.contains("done");
    R.push("tick=" + (on && q("#progress").textContent === "1 of " + want + " done" ? "ok" : on + "/" + q("#progress").textContent));
    q('[data-tick="' + id0 + '"]').click();
    R.push("untick=" + (q('[data-job="' + id0 + '"]').classList.contains("done") ? "stuck" : "ok"));
    q('[data-tick="' + id1 + '"]').click(); q('[data-tick="' + id0 + '"]').click();
    var m0 = q(".mstat").textContent;
    var saved = null; try { saved = JSON.parse(localStorage.getItem("home:" + HOME.id)); } catch(x){}
    R.push("saved=" + (saved && saved.ticks[id0] && saved.ticks[id1] && Object.keys(saved.ticks).length === 2 ? "ok" : "no"));
    R.push("month=" + JSON.stringify(m0));
    // look menu, then two stray taps (on a heading, and on <html> itself, which carries data-bg/data-font)
    q('[data-pop="look"]').click(); var opened = q("#pop-look").classList.contains("open");
    q('#pop-look [data-bg="night"]').click(); q('#pop-look [data-font="story"]').click();
    var root = document.documentElement, bg = root.getAttribute("data-bg"), font = root.getAttribute("data-font");
    q("#title").click();
    var after1 = root.getAttribute("data-bg") + "/" + root.getAttribute("data-font") + "/" + q("#pop-look").classList.contains("open");
    q('[data-pop="look"]').click(); root.click();
    var after2 = root.getAttribute("data-bg") + "/" + root.getAttribute("data-font") + "/" + q("#pop-look").classList.contains("open");
    R.push("look=" + (opened && bg === "night" && font === "story" ? "ok" : bg + "/" + font));
    R.push("strayTap=" + (after1 === "night/story/false" && after2 === "night/story/false" ? "ok" : after1 + " " + after2));
    q('[data-act="print"]').click();
    q('[data-act="ics"]').click();
    R.push("download=" + dl + (dl === HOME.ics.name + "|blob" ? " ok" : " WRONG"));
    if (!blob){ R.push("noBlob"); finish(); return; }
    R.push("blobType=" + blob.type);
    var fr = new FileReader();
    fr.onload = function(){ document.body.setAttribute("data-ics", String(fr.result).split(",")[1]); R.push("icsBytes=" + blob.size); finish(); };
    fr.onerror = function(){ R.push("readFail"); finish(); };
    fr.readAsDataURL(blob);
  } catch(ex){ R.push("EXCEPTION " + ex.message); errs++; finish(); }
}, 400);
})();
