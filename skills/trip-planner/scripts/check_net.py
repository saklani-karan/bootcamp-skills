#!/usr/bin/env python3
"""Can THIS sandbox reach the web? Run before building:   python3 scripts/check_net.py

Prints "internet: yes" or "internet: no (<why>)" and exits 0 / 1, within about 10 seconds.
It asks Wikipedia with the same User-Agent build_page.py uses (Wikipedia answers urllib's
default one with 403). ANY answer from the server - even 403 or 404 - means the web is
reachable. Only no answer at all (no DNS, refused, timed out, or a sandbox proxy that will
not open the connection) means no internet."""
import os, sys, threading, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_page import UA

URL = "https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&format=json"
result = {}


def probe():
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=8) as r:
            result["yes"] = f"HTTP {r.status}"
    except urllib.error.HTTPError as e:          # the server itself answered
        result["yes"] = f"HTTP {e.code}"
    except Exception as e:                       # URLError, timeout, proxy tunnel refused ...
        result["no"] = f"{type(e).__name__}: {getattr(e, 'reason', e)}"


t = threading.Thread(target=probe, daemon=True)
t.start()
t.join(10)                                       # bounds a DNS stall too, which timeout= does not
if "yes" in result:
    print(f"internet: yes ({result['yes']}) - build normally, without --no-net or --live-photos")
    sys.exit(0)
print(f"internet: no ({result.get('no', 'no answer within 10 s')}) - build with --no-net --live-photos")
sys.exit(1)
