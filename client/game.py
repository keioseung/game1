import pygame
import socket
import threading
import sys
import time
import pygame.mixer

WIDTH, HEIGHT = 960, 540
FPS = 60

SERVER_IP = '127.0.0.1'
SERVER_PORT = 9009

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('MMORPG Demo - Game')
clock = pygame.time.Clock()

# 캐릭터 정보
player_pos = [WIDTH//2, HEIGHT//2]
player_color = (0, 200, 255)
player_size = 32
nickname = ''

# 서버 연결
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((SERVER_IP, SERVER_PORT))
except Exception as e:
    print('서버 연결 실패:', e)
    sys.exit()

# 서버로부터 다른 유저 위치 수신
other_players = {}
chat_input = ''
chat_active = False
chat_messages = []
font = pygame.font.SysFont('malgungothic', 18)

friend_list = []
party_id = None
party_members = []
monsters = {}  # {id: (x, y, hp)}
level = 1
exp = 0
levelup_msg = ''
levelup_timer = 0
inventory = []

# 효과음 로드
try:
    snd_attack = pygame.mixer.Sound('resources/attack.wav')
    snd_levelup = pygame.mixer.Sound('resources/levelup.wav')
    snd_item = pygame.mixer.Sound('resources/item.wav')
except:
    snd_attack = snd_levelup = snd_item = None

player_anim_offset = 0
player_anim_dir = 1
monster_anim_offsets = {}

def recv_thread():
    global other_players, chat_messages, friend_list, party_id, party_members, monsters, level, exp, levelup_msg, levelup_timer, inventory
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            msg = data.decode()
            if msg.startswith('PLAYERS:'):
                # 예시: PLAYERS:nick1,x1,y1|nick2,x2,y2|...
                other_players = {}
                for entry in msg[8:].split('|'):
                    if entry:
                        nick, x, y = entry.split(',')
                        other_players[nick] = (int(x), int(y))
            elif msg.startswith('CHAT:'):
                chat_messages.append(msg[5:])
                if len(chat_messages) > 10:
                    chat_messages = chat_messages[-10:]
            elif msg.startswith('FRIEND_LIST:'):
                friend_list = msg[12:].split('|') if msg[12:] else []
                chat_messages.append(f'[친구목록] {", ".join(friend_list) if friend_list else "없음"}')
            elif msg.startswith('FRIEND_ADD_OK'):
                chat_messages.append('[친구추가 성공]')
            elif msg.startswith('FRIEND_ADD_FAIL'):
                chat_messages.append('[친구추가 실패]')
            elif msg.startswith('PARTY_CREATE_OK:'):
                party_id = msg.split(':')[1]
                chat_messages.append(f'[파티 생성] ID: {party_id}')
            elif msg.startswith('PARTY_CREATE_FAIL'):
                chat_messages.append('[파티 생성 실패]')
            elif msg.startswith('PARTY_INVITE_OK'):
                chat_messages.append('[파티 초대 성공]')
            elif msg.startswith('PARTY_INVITE_FAIL'):
                chat_messages.append('[파티 초대 실패]')
            elif msg.startswith('PARTY_LIST:'):
                party_members = msg[10:].split('|') if msg[10:] else []
                chat_messages.append(f'[파티원] {", ".join(party_members) if party_members else "없음"}')
            elif msg.startswith('MONSTERS:'):
                monsters = {}
                for entry in msg[9:].split('|'):
                    if entry:
                        mid, x, y, hp = entry.split(',')
                        monsters[int(mid)] = (int(x), int(y), int(hp))
            elif msg.startswith('LEVEL:'):
                _, nick, lv, xp, up = msg.split(':')
                if nick == nickname:
                    level = int(lv)
                    exp = int(xp)
                    if up == '1':
                        levelup_msg = f'레벨업! Lv.{level}'
                        levelup_timer = 120  # 2초
            elif msg.startswith('INVENTORY:'):
                _, nick, inv = msg.split(':', 2)
                if nick == nickname:
                    inventory = [tuple(x.split(',')) for x in inv.split('|') if x]
        except:
            break
threading.Thread(target=recv_thread, daemon=True).start()

def send_position():
    client_socket.sendall(f'POS:{nickname},{player_pos[0]},{player_pos[1]}'.encode())

# 로그인 후 닉네임을 받아옴 (실제론 main.py에서 전달)
nickname = input('닉네임을 입력하세요: ')

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if chat_active:
                if event.key == pygame.K_RETURN:
                    if chat_input.strip():
                        # 명령어 처리
                        if chat_input.startswith('/friend add '):
                            _, _, friendname = chat_input.split(' ', 2)
                            client_socket.sendall(f'FRIEND_ADD:{nickname}:{friendname}'.encode())
                        elif chat_input.startswith('/friend list'):
                            client_socket.sendall(f'FRIEND_LIST:{nickname}'.encode())
                        elif chat_input.startswith('/party create'):
                            client_socket.sendall(f'PARTY_CREATE:{nickname}'.encode())
                        elif chat_input.startswith('/party invite '):
                            if party_id:
                                _, _, invitee = chat_input.split(' ', 2)
                                client_socket.sendall(f'PARTY_INVITE:{party_id}:{invitee}'.encode())
                            else:
                                chat_messages.append('[파티 없음]')
                        elif chat_input.startswith('/party list'):
                            if party_id:
                                client_socket.sendall(f'PARTY_LIST:{party_id}'.encode())
                            else:
                                chat_messages.append('[파티 없음]')
                        elif chat_input == '/inv':
                            client_socket.sendall(f'INVENTORY:{nickname}'.encode())
                        else:
                            client_socket.sendall(f'CHAT:{nickname}:{chat_input}'.encode())
                    chat_input = ''
                    chat_active = False
                elif event.key == pygame.K_BACKSPACE:
                    chat_input = chat_input[:-1]
                else:
                    chat_input += event.unicode
            else:
                if event.key == pygame.K_RETURN:
                    chat_active = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # 가장 가까운 몬스터 찾기
            min_dist = 9999
            target_id = None
            for mid, (x, y, hp) in monsters.items():
                dist = ((mx-x)**2 + (my-y)**2)**0.5
                if dist < 40 and dist < min_dist:
                    min_dist = dist
                    target_id = mid
            if target_id:
                if snd_attack: snd_attack.play()
                client_socket.sendall(f'ATTACK:{nickname}:{target_id}'.encode())
    keys = pygame.key.get_pressed()
    moved = False
    if keys[pygame.K_w]:
        player_pos[1] -= 4
        moved = True
    if keys[pygame.K_s]:
        player_pos[1] += 4
        moved = True
    if keys[pygame.K_a]:
        player_pos[0] -= 4
        moved = True
    if keys[pygame.K_d]:
        player_pos[0] += 4
        moved = True
    if moved:
        player_anim_offset += player_anim_dir
        if abs(player_anim_offset) > 8:
            player_anim_dir *= -1
        send_position()
    # 반투명 패널
    panel = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    panel.fill((0,0,0,60))
    screen.blit(panel, (0,0))
    # 캐릭터(그림자+애니메이션)
    pygame.draw.ellipse(screen, (0,0,0,80), (player_pos[0], player_pos[1]+player_size-8, player_size, 12))
    pygame.draw.rect(screen, player_color, (player_pos[0], player_pos[1]+player_anim_offset, player_size, player_size))
    screen.blit(font.render(nickname, True, (255,255,255)), (player_pos[0], player_pos[1]-20))
    # 다른 유저
    for nick, (x, y) in other_players.items():
        if nick != nickname:
            pygame.draw.rect(screen, (255, 180, 0), (x, y, player_size, player_size))
            screen.blit(font.render(nick, True, (255,255,0)), (x, y-20))
    # 채팅창
    chat_box = pygame.Rect(10, HEIGHT-40, 400, 30)
    pygame.draw.rect(screen, (20,20,20), chat_box)
    pygame.draw.rect(screen, (100,100,255) if chat_active else (80,80,80), chat_box, 2)
    chat_surface = font.render(chat_input if chat_active else 'Enter: 채팅 입력', True, (200,200,255) if chat_active else (150,150,150))
    screen.blit(chat_surface, (chat_box.x+5, chat_box.y+5))
    # 채팅 메시지 표시
    for i, msg in enumerate(chat_messages):
        msg_surface = font.render(msg, True, (255,255,255))
        screen.blit(msg_surface, (10, HEIGHT-80-20*i))
    # 몬스터(그림자+애니메이션)
    for mid, (x, y, hp) in monsters.items():
        if mid not in monster_anim_offsets:
            monster_anim_offsets[mid] = 0
        monster_anim_offsets[mid] += (1 if mid%2==0 else -1)
        offset = monster_anim_offsets[mid]//4
        pygame.draw.ellipse(screen, (0,0,0,80), (x-16, y+20, 32, 12))
        pygame.draw.circle(screen, (200,50,50), (x, y+offset), 24)
        screen.blit(font.render(f'M{mid} HP:{hp}', True, (255,255,255)), (x-20, y-35+offset))
    # 레벨/경험치 표시
    screen.blit(font.render(f'Lv.{level} EXP:{exp}', True, (0,255,0)), (WIDTH-200, 10))
    if levelup_msg and levelup_timer > 0:
        if snd_levelup and levelup_timer == 120:
            snd_levelup.play()
        msg_surface = font.render(levelup_msg, True, (255,255,0))
        screen.blit(msg_surface, (WIDTH//2-60, 60))
        levelup_timer -= 1
    # 인벤토리 표시
    inv_y = 100
    screen.blit(font.render('인벤토리:', True, (255,255,255)), (WIDTH-200, inv_y))
    for i, (iname, cnt) in enumerate(inventory):
        if snd_item and iname == '포션' and int(cnt) == 1:
            snd_item.play()
        screen.blit(font.render(f'{iname} x{cnt}', True, (255,255,0)), (WIDTH-200, inv_y+25*(i+1)))
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
client_socket.close() 