import socket
import threading
import json
import base64
import queue
import tkinter as tk
from tkinter import scrolledtext
import sounddevice as sd

HOST = "127.0.0.1"
PORT = 5050

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
BLOCKSIZE = 1024

# walkie talkie client GUI
class WalkieTalkieClient:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Walkie-Talkie")
        self.root.geometry("560x420")

        self.conn = None
        self.running = False
        self.talking = False
        self.audio_queue = queue.Queue()

        self.input_stream = None
        self.output_stream = None

        self.build_gui()

    def build_gui(self) -> None:
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10)

        tk.Label(top_frame, text="Username:").pack(side=tk.LEFT, padx=5)

        self.username_entry = tk.Entry(top_frame, width=20)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        self.username_entry.insert(0, "Anonymous")
        self.username_entry.bind("<Button-1>", self.select_all_username)

        self.connect_button = tk.Button(
            self.root,
            text="Connect",
            width=20,
            command=self.connect_to_server
        )
        self.connect_button.pack(pady=10)

        self.status_label = tk.Label(self.root, text="Disconnected", fg="red")
        self.status_label.pack(pady=5)

        self.talk_button = tk.Button(
            self.root,
            text="Hold to Talk",
            width=20,
            height=3,
            state=tk.DISABLED
        )
        self.talk_button.pack(pady=20)

        self.talk_button.bind("<ButtonPress-1>", self.start_talking)
        self.talk_button.bind("<ButtonRelease-1>", self.stop_talking)

        self.root.bind("<KeyPress-space>", self.start_talking)
        self.root.bind("<KeyRelease-space>", self.stop_talking)

        self.log_box = scrolledtext.ScrolledText(self.root, width=48, height=12, state=tk.DISABLED)
        self.log_box.pack(padx=10, pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    # helper function to select all text
    def select_all_username(self, event=None) -> None:
        self.username_entry.focus_set()
        self.username_entry.select_range(0, tk.END)
        self.username_entry.icursor(tk.END)
        return "break"

    # helper function to log msgs in GUI
    def log(self, message: str) -> None:
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def send_json(self, message: dict) -> None:
        if self.conn:
            data = (json.dumps(message) + "\n").encode("utf-8")
            self.conn.sendall(data)

    def recv_lines(self):
        buffer = ""
        while self.running:
            data = self.conn.recv(65536)
            if not data:
                return
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    yield line

    def receiver_loop(self) -> None:
        try:
            for line in self.recv_lines():
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")

                if msg_type == "INFO":
                    self.root.after(0, lambda m=msg.get("message", ""): self.log("[INFO] " + m))

                elif msg_type == "ERROR":
                    self.root.after(0, lambda m=msg.get("message", ""): self.log("[ERROR] " + m))

                elif msg_type == "AUDIO":
                    payload = msg.get("payload")
                    sender = msg.get("from", "Unknown")
                    if isinstance(payload, str):
                        try:
                            chunk = base64.b64decode(payload.encode("ascii"))
                            self.audio_queue.put(chunk)
                        except Exception:
                            pass

                else:
                    self.root.after(0, lambda: self.log("[UNKNOWN] Message received"))

        except Exception:
            pass
        finally:
            self.running = False
            self.root.after(0, self.handle_disconnect)

    # audio callbacks for mic input
    def playback_callback(self, outdata, frames, time_info, status):
        try:
            chunk = self.audio_queue.get_nowait()
            needed = len(outdata)
            if len(chunk) < needed:
                chunk += b"\x00" * (needed - len(chunk))
            outdata[:] = chunk[:needed]
        except queue.Empty:
            outdata[:] = b"\x00" * len(outdata)

    def microphone_callback(self, indata, frames, time_info, status):
        if not self.running or not self.talking:
            return

        try:
            payload = base64.b64encode(bytes(indata)).decode("ascii")
            self.send_json({
                "type": "AUDIO",
                "payload": payload
            })
        except Exception:
            self.running = False

    # main logic that conencts to server and starts audio streams
    def connect_to_server(self) -> None:
        if self.running:
            return

        username = self.username_entry.get().strip()
        if not username:
            username = "Anonymous"

        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((HOST, PORT))
            self.running = True

            self.send_json({
                "type": "CONNECT",
                "username": username
            })

            self.input_stream = sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=BLOCKSIZE,
                callback=self.microphone_callback
            )

            self.output_stream = sd.RawOutputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=BLOCKSIZE,
                callback=self.playback_callback
            )

            self.input_stream.start()
            self.output_stream.start()

            threading.Thread(target=self.receiver_loop, daemon=True).start()

            self.status_label.config(text="Connected", fg="green")
            self.connect_button.config(text="Disconnect", command=self.disconnect_from_server)
            self.username_entry.config(state=tk.DISABLED)
            self.talk_button.config(state=tk.NORMAL)
            self.talk_button.focus_set()

            self.log("Connected to server.")

        except Exception as e:
            self.log(f"Connection failed: {e}")
            self.status_label.config(text="Disconnected", fg="red")

    def disconnect_from_server(self) -> None:
        self.running = False
        self.talking = False

        try:
            if self.conn:
                self.send_json({"type": "DISCONNECT"})
        except Exception:
            pass

        try:
            if self.input_stream:
                self.input_stream.stop()
                self.input_stream.close()
                self.input_stream = None
        except Exception:
            pass

        try:
            if self.output_stream:
                self.output_stream.stop()
                self.output_stream.close()
                self.output_stream = None
        except Exception:
            pass

        try:
            if self.conn:
                self.conn.close()
                self.conn = None
        except Exception:
            pass

        self.handle_disconnect()
        
    def start_talking(self, event=None) -> None:
        if self.running and not self.talking:
            self.talking = True
            self.log("Talking...")

    def stop_talking(self, event=None) -> None:
        self.talking = False
        self.log("Stopped talking.")

    def handle_disconnect(self) -> None:
        self.status_label.config(text="Disconnected", fg="red")
        self.connect_button.config(text="Connect", command=self.connect_to_server)
        self.username_entry.config(state=tk.NORMAL)
        self.talk_button.config(state=tk.DISABLED)
        self.log("Disconnected from server.")

    def on_close(self) -> None:
        self.running = False
        self.talking = False

        try:
            if self.conn:
                self.send_json({"type": "DISCONNECT"})
        except Exception:
            pass

        try:
            if self.input_stream:
                self.input_stream.stop()
                self.input_stream.close()
        except Exception:
            pass

        try:
            if self.output_stream:
                self.output_stream.stop()
                self.output_stream.close()
        except Exception:
            pass

        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass

        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = WalkieTalkieClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()