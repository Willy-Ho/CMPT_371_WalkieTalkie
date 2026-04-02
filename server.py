import socket
import threading
import json
import base64

HOST = "127.0.0.1"
PORT = 5050

clients = []
clients_lock = threading.Lock()


def send_json(conn: socket.socket, message: dict) -> None:
    data = (json.dumps(message) + "\n").encode("utf-8")
    conn.sendall(data)


def recv_lines(conn: socket.socket):
    buffer = ""
    while True:
        data = conn.recv(65536)
        if not data:
            return
        buffer += data.decode("utf-8")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line:
                yield line


def broadcast(message: dict, exclude: socket.socket | None = None) -> None:
    dead = []
    with clients_lock:
        for conn in clients:
            if conn is exclude:
                continue
            try:
                send_json(conn, message)
            except Exception:
                dead.append(conn)

        for conn in dead:
            if conn in clients:
                clients.remove(conn)
            try:
                conn.close()
            except Exception:
                pass


def handle_client(conn: socket.socket, addr) -> None:
    username = f"{addr[0]}:{addr[1]}"
    registered = False

    try:
        for line in recv_lines(conn):
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "CONNECT":
                requested_name = msg.get("username")
                if isinstance(requested_name, str) and requested_name.strip():
                    username = requested_name.strip()

                with clients_lock:
                    if conn not in clients:
                        clients.append(conn)

                registered = True
                send_json(conn, {
                    "type": "INFO",
                    "message": f"Connected as {username}. Hold SPACE to talk."
                })
                broadcast({
                    "type": "INFO",
                    "message": f"{username} joined."
                }, exclude=conn)

            elif msg_type == "AUDIO" and registered:
                payload = msg.get("payload")
                if not isinstance(payload, str):
                    continue

                broadcast({
                    "type": "AUDIO",
                    "from": username,
                    "payload": payload
                }, exclude=conn)

            elif msg_type == "DISCONNECT":
                break

    except Exception:
        pass

    finally:
        with clients_lock:
            if conn in clients:
                clients.remove(conn)

        if registered:
            broadcast({
                "type": "INFO",
                "message": f"{username} left."
            }, exclude=conn)

        try:
            conn.close()
        except Exception:
            pass


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    server.settimeout(1.0)

    print(f"[STARTING] Walkie-talkie server on {HOST}:{PORT}")

    try:
        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr),
                    daemon=True
                )
                thread.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server stopping.")
    finally:
        server.close()


if __name__ == "__main__":
    main()