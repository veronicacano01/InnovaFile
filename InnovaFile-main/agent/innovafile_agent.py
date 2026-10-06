"""Agente de escritorio de InnovaFile.

Selecciona una carpeta una sola vez y el agente vigila sus cambios.
Cada documento compatible se envía al servidor para que Gemini lo clasifique.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "agent_config.json"
SUPPORTED = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv", ".jpg", ".jpeg", ".png"}
MAX_SIZE = 50 * 1024 * 1024


def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def choose_folder():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title="Selecciona la carpeta que InnovaFile vigilará")
    root.destroy()
    return folder


def setup():
    import getpass
    print("\n=== InnovaFile · Configuración del agente ===\n")
    base_url = input("Dirección de InnovaFile [http://127.0.0.1:5000]: ").strip() or "http://127.0.0.1:5000"
    token = input("Token de sincronización de InnovaFile: ").strip()
    folder = choose_folder()
    if not token or not folder:
        print("Debes indicar el token y seleccionar una carpeta.")
        return False
    folder = str(Path(folder).resolve())
    save_config({"server_url": base_url.rstrip("/"), "token": token, "folder": folder})
    print(f"\nConfiguración guardada en: {CONFIG_FILE}")
    print(f"Carpeta vigilada: {folder}\n")
    return True


def send_file(path: Path, config):
    if not path.is_file() or path.suffix.lower() not in SUPPORTED:
        return
    try:
        size = path.stat().st_size
    except OSError:
        return
    if size <= 0 or size > MAX_SIZE:
        print(f"[OMITIDO] {path.name} (vacío o mayor a 50 MB)")
        return

    # Windows puede tardar un momento en terminar de escribir un archivo.
    time.sleep(1.2)
    for attempt in range(3):
        try:
            with path.open("rb") as fh:
                relative = path.relative_to(Path(config["folder"]).resolve()).as_posix()
                url = urljoin(config["server_url"] + "/", "documents/auto-import")
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {config['token']}"},
                    data={"source_path": relative},
                    files={"file": (path.name, fh, "application/octet-stream")},
                    timeout=300,
                )
            data = response.json() if response.content else {}
            if response.status_code == 401:
                print(f"[ERROR] Token no válido o revocado. Genera uno nuevo en InnovaFile.")
                return
            if response.status_code >= 400 or not data.get("ok"):
                raise RuntimeError(data.get("message", f"HTTP {response.status_code}"))
            status = data.get("status", "procesado")
            print(f"[{status.upper()}] {path.name} → {data.get('category', 'Otros')} ({data.get('confidence', 0)}%)")
            return
        except (OSError, requests.RequestException, ValueError, RuntimeError) as exc:
            if attempt == 2:
                print(f"[ERROR] {path.name}: {exc}")
            else:
                time.sleep(2)


def initial_scan(config):
    root = Path(config["folder"]).resolve()
    print(f"\nRevisando documentos existentes en: {root}")
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            send_file(path, config)


class Handler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.pending = {}
        self.lock = threading.Lock()

    def _queue(self, filename):
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() not in SUPPORTED:
            return
        with self.lock:
            old = self.pending.get(str(path))
            if old:
                old.cancel()
            timer = threading.Timer(1.5, self._process, args=(path,))
            timer.daemon = True
            self.pending[str(path)] = timer
            timer.start()

    def _process(self, path):
        with self.lock:
            self.pending.pop(str(path), None)
        send_file(path, self.config)

    def on_created(self, event):
        if not event.is_directory:
            self._queue(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._queue(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._queue(event.dest_path)


def main():
    config = load_config()
    if not config.get("server_url") or not config.get("token") or not config.get("folder"):
        if not setup():
            return 1
        config = load_config()

    folder = Path(config["folder"]).resolve()
    if not folder.is_dir():
        print(f"La carpeta configurada no existe: {folder}")
        print("Ejecuta CONFIGURAR_AGENTE.bat para seleccionar otra.")
        return 1

    initial_scan(config)
    observer = Observer()
    observer.schedule(Handler(config), str(folder), recursive=True)
    observer.start()
    print("\n✓ InnovaFile está vigilando la carpeta automáticamente.")
    print("Los documentos nuevos o modificados se analizarán con Gemini.")
    print("No cierres esta ventana mientras quieras mantener la sincronización.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
