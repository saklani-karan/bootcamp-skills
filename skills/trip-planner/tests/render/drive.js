<script>
/* test driver for a trip page, steps named in the hash:
     #play          click every control a reader can use, then write a report into body[data-r]
     #view-<id>     show section <id> (or "credits", "top") alone for a screenshot; no clicks
   Clicks are element.click() on the real controls - the page's own listeners run, nothing is faked. */
(function(){
  var step = location.hash.slice(1), wait = 15000;     /* virtual ms: photo lookups finish first */
  try{ localStorage.clear(); }catch(e){}
  function photos(){
    var boxes = document.querySelectorAll(".ph"), shown = 0, hidden = 0, grey = 0, keys = {}, k;
    for(var i = 0; i < boxes.length; i++){
      var cs = getComputedStyle(boxes[i]), m = boxes[i].className.match(/\bph-([A-Za-z0-9_-]+)/);
      if(!m) continue;
      var st = cs.display === "none" ? "hidden" : /url\(/.test(cs.backgroundImage) ? "shown" : "grey";
      if(st === "shown") shown++; else if(st === "hidden") hidden++; else grey++;
      keys[m[1]] = st;
    }
    var ks = Object.keys(keys), kshown = ks.filter(function(x){ return keys[x] === "shown"; });
    var cred = document.querySelector(".src .credit");
    return "photos: keys=" + ks.length + " loaded=" + kshown.length + " hidden=" + ks.filter(function(x){ return keys[x] === "hidden"; }).length +
      " grey=" + ks.filter(function(x){ return keys[x] === "grey"; }).length +
      " | boxes=" + (shown + hidden + grey) + " shown=" + shown + " hidden=" + hidden + " grey=" + grey +
      " | loaded-keys=" + kshown.join(",") +
      " | credit=" + (cred ? cred.textContent.replace(/\s+/g, " ").trim() : "none");
  }
  function play(){
    var ok = 0, bad = [];
    function t(cond, what){ if(cond) ok++; else bad.push(what); }
    /* booking checkboxes: tick, untick, tick - and the device remembers each state */
    var boxes = document.querySelectorAll('input[type="checkbox"][id^="bk-"]');
    for(var i = 0; i < boxes.length; i++){
      var b = boxes[i], key = "trip." + b.id;
      b.click(); t(b.checked && localStorage.getItem(key) === "1", b.id + " tick");
      b.click(); t(!b.checked && localStorage.getItem(key) === "0", b.id + " untick");
      b.click(); t(b.checked && localStorage.getItem(key) === "1", b.id + " re-tick");
    }
    /* contents board and the rail: each link lands on its own section */
    var links = document.querySelectorAll('.toc a[href^="#"], .rail-nav a[href^="#"]'), nl = 0;
    for(var j = 0; j < links.length; j++){
      var id = links[j].getAttribute("href").slice(1);
      links[j].click(); nl++;
      t(location.hash === "#" + id && !!document.getElementById(id), "link #" + id);
    }
    /* print */
    var p = document.getElementById("print"), before = PRINTS;
    if(p) p.click(); t(!!p && PRINTS === before + 1, "print button");
    var secs = document.querySelectorAll("section[id]").length;
    return "controls: checkboxes=" + boxes.length + " links=" + nl + " print=" + (p ? 1 : 0) +
      " | checks ok=" + ok + " failed=" + bad.length + (bad.length ? " (" + bad.join("; ") + ")" : "") +
      " | sections=" + secs + " wrap=" + (document.querySelector(".wrap .src") ? "whole" : "BROKEN");
  }
  if(step === "play"){
    setTimeout(function(){
      var r;
      try{ r = play(); }catch(e){ ERRS.push("driver: " + e.message); r = "controls: driver crashed"; }
      setTimeout(function(){
        var pe = ERRS.filter(function(x){ return /live photos:/.test(x); }).length;
        document.body.setAttribute("data-r", "errors=" + ERRS.length + (ERRS.length ? " " + ERRS.join(";") : "") +
          " | photo-errors=" + pe + " live=" + (typeof livePhotos === "function" ? 1 : 0) +
          " | " + r + " | " + photos());
      }, wait);
    }, 300);
  } else if(step.indexOf("view-") === 0){
    var v = step.slice(5);
    /* headless --screenshot ignores scrolling, so a view shows its block alone at the top:
       every other block of the page is hidden for the picture (the harness's change, not the page's) */
    function go(){
      if(v === "top") return;
      var el = v === "credits" ? document.querySelector(".src") : document.getElementById(v);
      if(!el) return;
      Array.prototype.forEach.call(document.querySelectorAll(".wrap > *, .rail-nav"), function(x){
        if(x !== el) x.style.display = "none"; });
    }
    setTimeout(go, 300);
  }
})();
</script>
