import sys, os
H = os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(H, "out"), exist_ok=True)
page = open(sys.argv[1], encoding="utf-8").read()
mode = sys.argv[2] if len(sys.argv) > 2 else "drive"
add = "<script>" + open(os.path.join(H, "drive.js")).read() + "</script>" if mode == "drive" else \
      "<script>document.body.classList.add('" + mode + "')</script>" if mode.startswith("p-") else ""
open(os.path.join(H, "out", "t.html"), "w", encoding="utf-8").write(page.replace("</body>", add + "</body>"))
