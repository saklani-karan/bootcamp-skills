/* Real clicks (element.click) and real typing into the focused box (execCommand insertText,
   which only lands if the box truly has focus). Never fires the event under test by hand. */
(function(){
var R = [], errs = 0;
window.addEventListener("error", function(){ errs++; });
window.confirm = function(){ return true; };   // the dialog is not under test
function q(s){ return document.querySelector(s); }
function cell(r,c){ return q('[data-rc="' + r + ',' + c + '"]'); }
function typeText(s){ for (var i = 0; i < s.length; i++) document.execCommand("insertText", false, s[i]); }
setTimeout(function(){
  try {
    var W = window.__crossword, E = W.entries, S = W.state();
    var e0 = E[0];
    cell(e0.cells[0][0], e0.cells[0][1]).click();
    R.push("focus=" + (document.activeElement && document.activeElement.id));
    var ans = e0.cells.map(function(rc){ return PUZZLE.cells[rc[0]][rc[1]].l; }).join("");
    typeText(ans);
    var got = e0.cells.map(function(rc){ return S.fill[rc[0] + "," + rc[1]] || "_"; }).join("");
    R.push("typed=" + (got === ans ? "ok" : got + "!=" + ans));
    R.push("clueDone=" + q('[data-entry="0"]').classList.contains("done"));
    // a crossing cell: click twice flips direction
    var keys = Object.keys(S.fill); var cross = null;
    E.forEach(function(e){ if (e.dir === "D") e.cells.forEach(function(rc){ e0.cells.forEach(function(a){ if (a[0]===rc[0]&&a[1]===rc[1]) cross = rc; }); }); });
    if (cross){ cell(cross[0],cross[1]).click(); var b1 = q("#cluebar").textContent; cell(cross[0],cross[1]).click(); var b2 = q("#cluebar").textContent; R.push("toggle=" + (b1 !== b2)); }
    // a wrong letter, then Check
    var e1 = E[1]; cell(e1.cells[1][0], e1.cells[1][1]).click();
    var right = PUZZLE.cells[e1.cells[1][0]][e1.cells[1][1]].l; typeText(right === "Q" ? "Z" : "Q");
    q('[data-act="check"]').click();
    R.push("wrongShown=" + document.querySelectorAll(".c.wrong").length + " msg=" + JSON.stringify(q("#msg").textContent));
    // backspace clears it
    cell(e1.cells[1][0], e1.cells[1][1]).click();
    q("#kb").dispatchEvent(new KeyboardEvent("keydown", {key: "Backspace", bubbles: true}));
    R.push("afterBack=" + (S.fill[e1.cells[1][0] + "," + e1.cells[1][1]] || "empty"));
    // clicking a clue moves the cursor to that word
    var lastLi = document.querySelectorAll(".clues li"); lastLi = lastLi[lastLi.length - 1];
    lastLi.click(); R.push("clueClick=" + lastLi.classList.contains("on"));
    // look menu
    q('[data-pop="look"]').click(); q('[data-bg="night"]').click();
    R.push("bg=" + document.documentElement.getAttribute("data-bg"));
    q('[data-pop="look"]').click(); q('[data-bg="sky"]').click();
    // help me -> whole puzzle
    q('[data-pop="reveal"]').click(); q('[data-act="reveal-all"]').click();
    R.push("done=" + q("#done").classList.contains("show") + " banner=" + JSON.stringify(q("#done").textContent));
    var stored = null; try { stored = JSON.parse(localStorage.getItem("crossword:" + PUZZLE.id)); } catch(x){}
    R.push("saved=" + (stored ? Object.keys(stored.fill).length : "none") + "/" + Object.keys(S.fill).length);
  } catch(ex){ R.push("EXCEPTION " + ex.message); errs++; }
  document.body.setAttribute("data-r", "errors=" + errs + " | " + R.join(" | "));
}, 400);
})();
