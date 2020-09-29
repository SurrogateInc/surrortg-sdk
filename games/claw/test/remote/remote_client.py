import keyboard
import socket

# Server IP or Hostname (hostname -I on the server)
HOST = "10.20.65.101"  # = claw1, '10.20.65.102' = claw2

# Pick an open Port (1000+ recommended), must match the server port
PORT = 12345
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

KEYS = ["w", "a", "s", "d", "space"]
key_down_dict = {key: False for key in KEYS}


def send_cmd(cmd):
    s.send(cmd.encode())
    reply = s.recv(1024).decode("utf-8")
    print(reply)


def get_command():
    if key_down_dict["space"]:
        return "b"

    cmd = ""
    if not (key_down_dict["a"] and key_down_dict["d"]):
        if key_down_dict["a"]:
            cmd += "-1"
        elif key_down_dict["d"]:
            cmd += "1"
        else:
            cmd += "0"
    else:
        cmd += "0"

    cmd += ","

    if not (key_down_dict["w"] and key_down_dict["s"]):
        if key_down_dict["w"]:
            cmd += "1"
        elif key_down_dict["s"]:
            cmd += "-1"
        else:
            cmd += "0"
    else:
        cmd += "0"

    return cmd


def check_key(key):
    if keyboard.is_pressed(key):
        if not key_down_dict[key]:
            key_down_dict[key] = True
            # print(f"{key} down")

            send_cmd(get_command())
    elif key_down_dict[key]:
        key_down_dict[key] = False
        # print(f"{key} up")

        send_cmd(get_command())


while True:
    for key in KEYS:
        check_key(key)

    if keyboard.is_pressed("Esc"):
        send_cmd("exit")
        print()
        break
