/* ---------- photos named by Wikipedia article ----------
   Each entry in TRIP.photos names an English Wikipedia article ("wiki"). Online, the
   page asks Wikipedia for that article's main image and Commons for its credit.
   Only freely licensed Commons images are shown, and each is credited. With no
   network, no free image, or no answer within 20 seconds, that photo's box is
   hidden rather than left grey.
   Claude/Copilot copy (assets/, 2026-10-07): differs from gemini-gem/live-photos.js in two
   ways - credit text is read through an inert DOMParser document (the Commons "Artist" field
   is editable HTML and must never run), and a fault in this code, as opposed to having no
   network, hides every photo and is re-thrown so it reaches window.onerror (tests count it). */
function livePhotos(t){
  var css = document.getElementById("photos"), specs = {}, order = [], credit = {}, done = {};
  A(t.photos).forEach(function(p){
    if(p && /^[A-Za-z0-9_-]+$/.test(String(p.key)) && !specs[p.key]){ specs[p.key] = p; order.push(p.key); }
  });
  function rule(s){ css.appendChild(document.createTextNode("\n" + s)); }
  function hide(k){ if(done[k]) return; done[k] = 1; rule(".ph-" + k + "{display:none}"); }
  function show(k, src){ if(done[k]) return; done[k] = 1; rule(".ph-" + k + '{background-image:url("' + String(src).replace(/["\\\n]/g, "") + '")}'); }
  function credits(){
    var list = order.filter(function(k){ return credit[k]; }).map(function(k){ return credit[k]; });
    var p = document.querySelector(".src .credit");
    if(p) p.innerHTML = PHOTO_LINE + (list.length ? list.join(" &middot; ") + "." : "No photographs loaded.");
  }
  /* a failure that comes from the network (offline, refused, bad reply) is marked .net: that is normal */
  function net(e){ e = e || new Error("network"); e.net = 1; throw e; }
  function get(u){ return fetch(u).then(function(r){ if(!r.ok) net(new Error(r.status)); return r.json().catch(net); }, net); }
  function fault(e){ if(e && e.net) return; setTimeout(function(){ throw new Error("live photos: " + (e && e.message || e)); }, 0); }
  function text(h){
    var doc = new DOMParser().parseFromString(String(h || ""), "text/html");  /* inert: no script, no loads */
    return ((doc.body && doc.body.textContent) || "").replace(/\s+/g, " ").trim();
  }

  /* every photo box on the page; a box whose key has no article is hidden at once */
  var keys = {};
  Array.prototype.forEach.call(document.querySelectorAll(".ph"), function(el){
    el.className.split(/\s+/).forEach(function(c){ if(/^ph-[A-Za-z0-9_-]+$/.test(c)) keys[c.slice(3)] = 1; });
  });
  var want = [];
  Object.keys(keys).forEach(function(k){ if(specs[k] && specs[k].wiki) want.push({k: k, title: String(specs[k].wiki)}); else hide(k); });
  if(!want.length) return;
  setTimeout(function(){ want.forEach(function(b){ hide(b.k); }); }, 20000);

  for(var i = 0; i < want.length; i += 40) (function(batch){
    var titles = batch.map(function(b){ return b.title; });
    get("https://en.wikipedia.org/w/api.php?action=query&format=json&formatversion=2&origin=*&redirects=1&prop=pageimages&piprop=thumbnail|name&pithumbsize=960&pilimit=50&titles=" + encodeURIComponent(titles.join("|")))
    .then(function(r){
      var qy = r.query || {}, to = {}, page = {};
      (qy.normalized || []).concat(qy.redirects || []).forEach(function(m){ to[m.from] = m.to; });
      (qy.pages || []).forEach(function(p){ page[p.title] = p; });
      var found = [];
      batch.forEach(function(b){
        var x = b.title, hop = 0; while(to[x] && hop++ < 3) x = to[x];
        var p = page[x];
        if(p && p.thumbnail && p.pageimage) found.push({b: b, src: p.thumbnail.source, file: "File:" + p.pageimage}); else hide(b.k);
      });
      if(!found.length) return;
      return get("https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&origin=*&prop=imageinfo&iiprop=extmetadata&iiextmetadatafilter=Artist|LicenseShortName&titles=" + encodeURIComponent(found.map(function(f){ return f.file; }).join("|")))
      .then(function(c){
        var info = {}, norm = {};
        ((c.query || {}).normalized || []).forEach(function(m){ norm[m.from] = m.to; });
        ((c.query || {}).pages || []).forEach(function(p){ if(!p.missing && p.imageinfo && p.imageinfo[0]) info[p.title] = p.imageinfo[0].extmetadata || {}; });
        found.forEach(function(f){
          var m = info[norm[f.file] || f.file];
          if(!m){ hide(f.b.k); return; }  /* not on Commons: not freely licensed, so not shown */
          var who = text((m.Artist || {}).value).slice(0, 70) || "unknown", lic = text((m.LicenseShortName || {}).value) || "licence unknown";
          if(done[f.b.k]) return;
          show(f.b.k, f.src);
          credit[f.b.k] = E(specs[f.b.k].label || f.b.k) + " &mdash; " + E(who) + ", " + E(lic);
        });
        credits();
      });
    })
    .catch(function(e){ batch.forEach(function(b){ hide(b.k); }); fault(e); });
  })(want.slice(i, i + 40));
}
