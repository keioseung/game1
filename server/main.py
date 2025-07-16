import socket
import threading

HOST = '0.0.0.0'
PORT = 9009

clients = []

def handle_client(conn, addr):
    print(f'클라이언트 접속: {addr}')
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode()
            print(f'[{addr}] {msg}')
            if msg.startswith('LOGIN:'):
                nickname = msg.split(':', 1)[1]
                conn.sendall(f'WELCOME:{nickname}'.encode())
        except:
            break
    print(f'클라이언트 연결 종료: {addr}')
    conn.close()
    clients.remove(conn)

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f'Server listening on {HOST}:{PORT}')
    while True:
        conn, addr = server_socket.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    main() 