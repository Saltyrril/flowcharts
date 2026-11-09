"""Настольный режим: своё окно без адресной строки (Edge/Chrome --app), сервер закрывается вместе с окном."""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from .server import make_server, STATE

IDLE_AFTER_PING = 8.0     # секунд тишины после закрытия окна -> выход
START_TIMEOUT = 45.0      # сколько ждать первого обращения окна


def _find_browser():
    cands = []
    for env in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            cands += [os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
                      os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                      os.path.join(base, "Chromium", "Application", "chrome.exe")]
    cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    for name in ("msedge", "google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            cands.append(p)
    return next((c for c in cands if c and os.path.exists(c)), None)


def run():
    srv = make_server(0)                       # свободный порт
    port = srv.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    if os.environ.get("GOSTFLOW_NOBROWSER") != "1":
        exe = _find_browser()
        if exe:
            profile = os.path.join(tempfile.gettempdir(), "gostflow_profile")
            subprocess.Popen([exe, f"--app={url}", "--window-size=1320,900", f"--user-data-dir={profile}",
                              "--no-first-run", "--disable-extensions"])
        else:
            webbrowser.open(url)
    t0 = time.time()
    while True:                                # ждём, пока окно живо (оно пингует сервер)
        time.sleep(1.0)
        last = STATE["last_ping"]
        if last == 0.0 and time.time() - t0 > START_TIMEOUT:
            break
        if last and time.time() - last > IDLE_AFTER_PING:
            break
    srv.shutdown()
    return 0


def main():
    if sys.stdout is None:                     # режим без консоли (--noconsole)
        sys.stdout = sys.stderr = open(os.devnull, "w")
    sys.exit(run())
