/* ---------- photos named by Wikipedia article ----------
   A quiz may carry "wiki": {key: "Article title"} instead of stored photos. Online,
   the page asks Wikipedia for each article's main image and Commons for its credit.
   Only freely licensed Commons images are shown. Stored photos always win. With no
   network, or no free image, that photo's box is hidden rather than left grey. */
function livePhotos(){
  var css = $("photos"), want = {}, n = 0;
  LIB.forEach(function(q){
    var w = q.wiki || {};
    Object.keys(w).forEach(function(k){
      if(css.textContent.indexOf(".ph-" + k + "{") >= 0) return;
      var lang = /^[a-z-]{2,12}$/.test(q.wikiLang || "") ? q.wikiLang : "en";
      (want[lang] = want[lang] || []).push({k:k, title:String(w[k]), q:q}); n++;
    });
  });
  if(!n) return;
  function rule(s){ css.appendChild(document.createTextNode("\n" + s)); }
  function hide(k){ rule(".ph-" + k + "{display:none}.ph-" + k + "+.credit{display:none}"); }
  function get(u){ return fetch(u).then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); }); }
  function text(h){ /* parsed in a detached document, so no script or handler in a credit can run */ var d = new DOMParser().parseFromString(String(h || ""), "text/html"); return (d.documentElement.textContent || "").replace(/\s+/g, " ").trim(); }
  Object.keys(want).forEach(function(lang){
    var items = want[lang];
    for(var i = 0; i < items.length; i += 40) (function(batch){
      var titles = batch.map(function(b){ return b.title; });
      get("https://" + lang + ".wikipedia.org/w/api.php?action=query&format=json&formatversion=2&origin=*&redirects=1&prop=pageimages&piprop=thumbnail|name&pithumbsize=960&titles=" + encodeURIComponent(titles.join("|")))
      .then(function(r){
        var qy = r.query || {}, to = {}, page = {};
        (qy.normalized || []).concat(qy.redirects || []).forEach(function(m){ to[m.from] = m.to; });
        (qy.pages || []).forEach(function(p){ page[p.title] = p; });
        var found = [];
        batch.forEach(function(b){
          var t = b.title, hop = 0; while(to[t] && hop++ < 3) t = to[t];
          var p = page[t];
          if(p && p.thumbnail && p.pageimage) found.push({b:b, src:p.thumbnail.source, file:"File:" + p.pageimage}); else hide(b.k);
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
            var who = text((m.Artist || {}).value) || "unknown", lic = text((m.LicenseShortName || {}).value) || "licence unknown";
            f.b.q.credits = f.b.q.credits || {};
            f.b.q.credits[f.b.k] = who + ", " + lic + " · Wikimedia Commons";
            /* a card already on screen was drawn before this credit arrived: fill it in */
            Array.prototype.forEach.call(document.querySelectorAll(".ph-" + f.b.k), function(el){
              var nx = el.nextElementSibling;
              if(nx && nx.className === "credit") nx.textContent = "Photo: " + f.b.q.credits[f.b.k];
            });
            rule(".ph-" + f.b.k + '{background-image:url("' + String(f.src).replace(/["\\\n]/g, "") + '")}');
          });
        });
      })
      .catch(function(){ batch.forEach(function(b){ hide(b.k); }); });
    })(items.slice(i, i + 40));
  });
}

