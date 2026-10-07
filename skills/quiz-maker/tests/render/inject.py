#!/usr/bin/env python3
"""inject.py <built-quiz.html>  ->  out/t.html: the quiz + an error logger + the click driver + a report.
Everything resolves relative to this file, so it runs from wherever the skill lives."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
s = open(sys.argv[1], encoding="utf-8").read()
s = s.replace("<head>", '<head><script>var ERRS=[];window.onerror=function(m,u,l){ERRS.push(m+"@"+l)};</script>', 1)
drive = open(os.path.join(HERE, "drive.js"), encoding="utf-8").read()
report = ('<script>setTimeout(function(){var h=document.querySelector(".tiles");document.body.setAttribute("data-r",'
          '"errors="+ERRS.length+" "+ERRS.join(";")+" | games="+(h?h.textContent.replace(/\\s+/g," "):"none")+'
          '" | players="+[].map.call(document.querySelectorAll(".hist td b"),function(b){return b.textContent}).slice(0,1));},2500)</script>')
i = s.rindex("</body>")
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
open(os.path.join(HERE, "out", "t.html"), "w", encoding="utf-8").write(s[:i] + drive + report + s[i:])
