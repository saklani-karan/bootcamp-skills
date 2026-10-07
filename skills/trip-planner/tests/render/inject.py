#!/usr/bin/env python3
"""inject.py <built-trip.html>  ->  out/t.html: the page + an error logger + the click driver.
The logger and a print stub go in first, before the page's own scripts; the driver goes last.
Everything resolves relative to this file, so it runs from wherever the skill lives."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
s = open(sys.argv[1], encoding="utf-8").read()
head = ('<script>var ERRS=[],PRINTS=0;window.onerror=function(m,u,l){ERRS.push(m+"@"+l)};'
        'window.addEventListener("unhandledrejection",function(e){ERRS.push("promise: "+e.reason)});'
        'window.print=function(){PRINTS++};</script>\n')    # a real print dialog would hang headless Chrome
drive = open(os.path.join(HERE, "drive.js"), encoding="utf-8").read()
# build_page.py writes no <html>/<head>/<body>: put the logger first and the driver last
s = head + s + "\n" + drive
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
open(os.path.join(HERE, "out", "t.html"), "w", encoding="utf-8").write(s)
