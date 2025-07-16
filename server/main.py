import socket
import threading
from db import register_user, login_user, add_friend, get_friends, create_party, invite_party, get_party_members, add_exp_and_levelup, add_item_to_user, get_inventory
import random
import time

HOST = '0.0.0.0'
PORT = 9009

clients = []
players = {}  # {nickname: (conn, x, y)}

monsters = {}  # {monster_id: {'x': int, 'y': int, 'hp': int}}
monster_id_counter = 1

def spawn_monster():
    global monster_id_counter
    x = random.randint(100, 800)
    y = random.randint(100, 400)
    hp = 30
    mid = monster_id_counter
    monsters[mid] = {'x': x, 'y': y, 'hp': hp}
    monster_id_counter += 1

def monster_broadcast():
    msg = 'MONSTERS:' + '|'.join(f'{mid},{m["x"]},{m["y"]},{m["hp"]}' for mid, m in monsters.items())
    for c, _, _ in players.values():
        c.sendall(msg.encode())

def monster_loop():
    while True:
        if len(monsters) < 5:
            spawn_monster()
            monster_broadcast()
        time.sleep(5)
import threading
threading.Thread(target=monster_loop, daemon=True).start()

def handle_client(conn, addr):
    print(f'클라이언트 접속: {addr}')
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode()
            print(f'[{addr}] {msg}')
            if msg.startswith('REGISTER:'):
                # 회원가입 처리
                try:
                    _, username, password = msg.split(':', 2)
                    if register_user(username, password):
                        conn.sendall('REGISTER_OK'.encode())
                    else:
                        conn.sendall('REGISTER_FAIL'.encode())
                except:
                    conn.sendall('REGISTER_FAIL'.encode())
            elif msg.startswith('LOGIN:'):
                # 로그인 처리
                try:
                    _, username, password = msg.split(':', 2)
                    if login_user(username, password):
                        conn.sendall(f'LOGIN_OK:{username}'.encode())
                    else:
                        conn.sendall('LOGIN_FAIL'.encode())
                except:
                    conn.sendall('LOGIN_FAIL'.encode())
            elif msg.startswith('POS:'):
                # 위치 동기화
                try:
                    _, data = msg.split(':', 1)
                    nickname, x, y = data.split(',')
                    x, y = int(x), int(y)
                    players[nickname] = (conn, x, y)
                    # 모든 유저에게 위치 브로드캐스트
                    player_str = '|'.join(f'{n},{px},{py}' for n, (_, px, py) in players.items())
                    for c, _, _ in players.values():
                        c.sendall(f'PLAYERS:{player_str}'.encode())
                except:
                    pass
            elif msg.startswith('CHAT:'):
                # 채팅 브로드캐스트
                try:
                    _, nickname, chat = msg.split(':', 2)
                    chat_msg = f'{nickname}: {chat}'
                    for c, _, _ in players.values():
                        c.sendall(f'CHAT:{chat_msg}'.encode())
                except:
                    pass
            elif msg.startswith('FRIEND_ADD:'):
                try:
                    _, username, friendname = msg.split(':', 2)
                    if add_friend(username, friendname):
                        conn.sendall('FRIEND_ADD_OK'.encode())
                    else:
                        conn.sendall('FRIEND_ADD_FAIL'.encode())
                except:
                    conn.sendall('FRIEND_ADD_FAIL'.encode())
            elif msg.startswith('FRIEND_LIST:'):
                try:
                    _, username = msg.split(':', 1)
                    friends = get_friends(username)
                    conn.sendall(f'FRIEND_LIST:{"|".join(friends)}'.encode())
                except:
                    conn.sendall('FRIEND_LIST:'.encode())
            elif msg.startswith('PARTY_CREATE:'):
                try:
                    _, leadername = msg.split(':', 1)
                    party_id = create_party(leadername)
                    if party_id:
                        conn.sendall(f'PARTY_CREATE_OK:{party_id}'.encode())
                    else:
                        conn.sendall('PARTY_CREATE_FAIL'.encode())
                except:
                    conn.sendall('PARTY_CREATE_FAIL'.encode())
            elif msg.startswith('PARTY_INVITE:'):
                try:
                    _, party_id, username = msg.split(':', 2)
                    if invite_party(int(party_id), username):
                        conn.sendall('PARTY_INVITE_OK'.encode())
                    else:
                        conn.sendall('PARTY_INVITE_FAIL'.encode())
                except:
                    conn.sendall('PARTY_INVITE_FAIL'.encode())
            elif msg.startswith('PARTY_LIST:'):
                try:
                    _, party_id = msg.split(':', 1)
                    members = get_party_members(int(party_id))
                    conn.sendall(f'PARTY_LIST:{"|".join(members)}'.encode())
                except:
                    conn.sendall('PARTY_LIST:'.encode())
            elif msg.startswith('ATTACK:'):
                try:
                    _, nickname, mid = msg.split(':', 2)
                    mid = int(mid)
                    if mid in monsters:
                        monsters[mid]['hp'] -= 10
                        if monsters[mid]['hp'] <= 0:
                            del monsters[mid]
                            # 경험치 지급 및 레벨업
                            result = add_exp_and_levelup(nickname, 20)
                            if result:
                                level, exp, leveled_up = result
                                for c, _, _ in players.values():
                                    c.sendall(f'LEVEL:{nickname}:{level}:{exp}:{int(leveled_up)}'.encode())
                            # 아이템 드랍 (50% 확률)
                            if random.random() < 0.5:
                                itemname = random.choice(['포션', '골드', '검', '방패'])
                                add_item_to_user(nickname, itemname)
                                # 인벤토리 갱신
                                items = get_inventory(nickname)
                                inv_str = '|'.join(f'{n},{c}' for n, c in items)
                                for c, _, _ in players.values():
                                    c.sendall(f'INVENTORY:{nickname}:{inv_str}'.encode())
                        monster_broadcast()
                except:
                    pass
            elif msg.startswith('INVENTORY:'):
                try:
                    _, username = msg.split(':', 1)
                    items = get_inventory(username)
                    inv_str = '|'.join(f'{n},{c}' for n, c in items)
                    for c, _, _ in players.values():
                        c.sendall(f'INVENTORY:{username}:{inv_str}'.encode())
                except:
                    pass
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