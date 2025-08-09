import json
import queue
import socket
import sys
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 55555
PROJECT = sys.argv[1] if len(sys.argv) > 1 else "default"


def sender_thread(q):
    s = socket.socket()
    s.connect(("127.0.0.1", PORT))
    while True:
        msg = q.get()
        s.send(msg.encode())


def gui():
    root = tk.Tk()
    root.title(f"Master-AI ▸ {PROJECT}")
    log = ScrolledText(root, width=90, height=26, state="disabled")
    log.pack(padx=6, pady=6)
    entry = tk.Entry(root, width=90)
    entry.pack(padx=6, pady=4)
    outq = queue.Queue()
    threading.Thread(target=sender_thread, args=(outq,), daemon=True).start()

    def write(m):
        log["state"] = "normal"
        log.insert(tk.END, m + "\n")
        log["state"] = "disabled"
        log.see(tk.END)

    def on_enter(e=None):
        txt = entry.get().strip()
        entry.delete(0, tk.END)
        if txt:
            write("▶ " + txt)
            outq.put(json.dumps({"project": PROJECT, "msg": txt}))

    entry.bind("<Return>", on_enter)
    root.mainloop()


if __name__ == "__main__":
    gui()
