/* Real clicks only (element.click). Never fires the event under test by hand. */
(function(){
var R = [], errs = 0;
window.addEventListener("error", function(){ errs++; });
function q(s){ return document.querySelector(s); }
function firstRow(){ var td = document.querySelectorAll("#s-debts tbody tr td"); return td.length > 1 ? td[1].textContent : "none"; }
setTimeout(function(){
  try {
    var hasDebt = !!PLAN.debts.length;
    R.push("answer=" + (q("#s-answer .answer") ? "yes" : "no"));
    if (hasDebt){
      var startView = q(".tabs button.on").getAttribute("data-view");
      R.push("start=" + startView + " first=" + firstRow());
      var other = startView === "avalanche" ? "snowball" : "avalanche";
      q('[data-view="' + other + '"]').click();
      R.push("clicked=" + q(".tabs button.on").getAttribute("data-view") + " first=" + firstRow() +
             " expected=" + PLAN.strategies[other].order[0].name);
      R.push("dots=" + document.querySelectorAll("#chart circle").length + "/" + PLAN.debts.length);
      R.push("lines=" + document.querySelectorAll("#chart path").length);
      q('[data-view="' + startView + '"]').click();
      R.push("back=" + q(".tabs button.on").getAttribute("data-view"));
    }
    q('[data-pop="look"]').click(); q('[data-bg="night"]').click();
    R.push("bg=" + document.documentElement.getAttribute("data-bg"));
    R.push("fit=" + (q(".status.ok") ? "ok" : q(".status.short") ? "short" : "none"));
    var stored = null; try { stored = JSON.parse(localStorage.getItem("money-plan:" + PLAN.id)); } catch(x){}
    R.push("saved=" + (stored ? stored.look.bg : "none"));
  } catch(ex){ R.push("EXCEPTION " + ex.message); errs++; }
  document.body.setAttribute("data-r", "errors=" + errs + " | " + R.join(" | "));
}, 400);
})();
