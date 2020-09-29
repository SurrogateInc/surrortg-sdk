import socket
import logging
import asyncio
from games.claw.claw_machine import ClawJoystick, ClawButton

logging.getLogger().setLevel(logging.INFO)

# Connect the socket
# Server IP or Hostname (hostname -I)
HOST = "10.20.65.101"  # = claw1, '10.20.65.102' = claw2
# Pick an open Port (1000+ recommended), must match the client port
PORT = 12345
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# this fixes 'OSError: [Errno 98] Address already in use when restarting
# program fast
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
logging.info("Socket created")
s.bind((HOST, PORT))
s.listen(5)
conn, addr = s.accept()
logging.info("Connected")


async def main():
    joystick = ClawJoystick()
    button = ClawButton()
    while True:
        data = conn.recv(1024).decode("utf-8")
        logging.info(f"'{data}' received")
        reply = f"'{data}' received"

        if data == "b":
            await button.on()
        elif data == "exit" or data == "":
            conn.send(b"Exiting")
            break
        else:
            coords = data.split(",")
            await joystick.handle_coordinates(int(coords[0]), int(coords[1]))

        conn.send(reply.encode())
    conn.close()
    await joystick.shutdown()
    await button.shutdown()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
