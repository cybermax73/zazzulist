"""Mini client Chrome DevTools Protocol (stdlib only) pour piloter la page dans Edge headless.

Usage : APP_PORT=8080 [APP_MOBILE=1] python tools/cdp_test.py test.js
  test.js = une expression JavaScript par ligne (évaluée dans la page, résultat affiché),
  `sleep N` pour attendre N secondes, `#` pour un commentaire.
Prérequis : la page servie sur http://127.0.0.1:$APP_PORT/ (cd docs && python -m http.server 8080).
"""
import json, os, socket, struct, subprocess, sys, time, urllib.request

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 9333
proc = subprocess.Popen([EDGE, "--headless=new", "--disable-gpu", "--no-first-run", f"--remote-debugging-port={PORT}",
                         "--user-data-dir=" + os.path.join(os.path.dirname(os.path.abspath(__file__)), ".edgeprofile"), "about:blank"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(50):
    try:
        targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
    except Exception: time.sleep(0.2)
ws_url = [t for t in targets if t["type"] == "page"][0]["webSocketDebuggerUrl"]
host, path = ws_url.split("//")[1].split("/", 1)
h, p = host.split(":")
s = socket.create_connection((h, int(p)))
s.send((f"GET /{path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
buf = b""
while b"\r\n\r\n" not in buf: buf += s.recv(4096)
buf = buf.split(b"\r\n\r\n", 1)[1]

def send(method, params=None, _id=[0]):
    _id[0] += 1
    data = json.dumps({"id": _id[0], "method": method, "params": params or {}}).encode()
    hdr = bytearray([0x81])
    n = len(data)
    if n < 126: hdr.append(0x80 | n)
    elif n < 65536: hdr += bytes([0x80 | 126]) + struct.pack(">H", n)
    else: hdr += bytes([0x80 | 127]) + struct.pack(">Q", n)
    mask = b"\x00\x00\x00\x00"
    s.send(bytes(hdr) + mask + data)
    return _id[0]

def recv():
    global buf
    while True:
        while len(buf) < 2: buf += s.recv(65536)
        n = buf[1] & 0x7F; off = 2
        if n == 126: n = struct.unpack(">H", buf[2:4])[0]; off = 4
        elif n == 127: n = struct.unpack(">Q", buf[2:10])[0]; off = 10
        while len(buf) < off + n: buf += s.recv(65536)
        frame = buf[off:off + n]; buf = buf[off + n:]
        return json.loads(frame)

def call(method, params=None):
    i = send(method, params)
    while True:
        m = recv()
        if m.get("id") == i: return m.get("result", m)

def js(expr):
    r = call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    if "exceptionDetails" in r: return "EXC: " + json.dumps(r["exceptionDetails"].get("exception", {}).get("description", r["exceptionDetails"]))[:300]
    return r["result"].get("value")

call("Page.enable"); call("Runtime.enable")
if os.environ.get("APP_MOBILE"):  # émulation téléphone : APP_MOBILE=1 (largeur 400 px, tactile)
    call("Emulation.setDeviceMetricsOverride", {"width": 400, "height": 800, "deviceScaleFactor": 2, "mobile": True})
    call("Emulation.setTouchEmulationEnabled", {"enabled": True})
call("Page.navigate", {"url": "http://127.0.0.1:" + os.environ.get("APP_PORT","8765") + "/"})
time.sleep(3)
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.rstrip("\n")
    if not line.strip() or line.startswith("#"): continue
    if line.startswith("sleep "): time.sleep(float(line[6:])); continue
    print(">>", line[:90]); print("  ", js(line))
proc.kill()
