import pygame
import socket
import sys
import threading
import time

WIDTH, HEIGHT = 960, 540
FPS = 60

# 서버 정보
SERVER_IP = '127.0.0.1'
SERVER_PORT = 9009

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('MMORPG Demo Client')
clock = pygame.time.Clock()

# 로그인 화면
font = pygame.font.SysFont('malgungothic', 32)
input_box = pygame.Rect(350, 200, 260, 50)
color_inactive = pygame.Color('lightskyblue3')
color_active = pygame.Color('dodgerblue2')
color = color_inactive
active = False
text = ''

login_mode = 'login'  # 'login' or 'register'
password = ''
input_box_pw = pygame.Rect(350, 270, 260, 50)
active_pw = False
color_pw = color_inactive
msg = ''

# 서버 연결
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
except Exception as e:
    print('서버 연결 실패:', e)
    sys.exit()

# 서버 응답 수신 스레드
response = ''
def recv_thread():
    global response
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            response = data.decode()
        except:
            break
threading.Thread(target=recv_thread, daemon=True).start()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_box.collidepoint(event.pos):
                active = True
            else:
                active = False
            color = color_active if active else color_inactive
            if input_box_pw.collidepoint(event.pos):
                active_pw = True
            else:
                active_pw = False
            color_pw = color_active if active_pw else color_inactive
        if event.type == pygame.KEYDOWN:
            if active:
                if event.key == pygame.K_RETURN:
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode
            if active_pw:
                if event.key == pygame.K_RETURN:
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    password = password[:-1]
                else:
                    password += event.unicode
            if event.key == pygame.K_TAB:
                login_mode = 'register' if login_mode == 'login' else 'login'
            if event.key == pygame.K_RETURN:
                if login_mode == 'login':
                    client_socket.sendall(f'LOGIN:{text}:{password}'.encode())
                else:
                    client_socket.sendall(f'REGISTER:{text}:{password}'.encode())
                time.sleep(0.2)
                if response.startswith('LOGIN_OK'):
                    msg = '로그인 성공!'
                elif response == 'LOGIN_FAIL':
                    msg = '로그인 실패!'
                elif response == 'REGISTER_OK':
                    msg = '회원가입 성공!'
                elif response == 'REGISTER_FAIL':
                    msg = '회원가입 실패!'
                else:
                    msg = ''

    screen.fill((30, 30, 50))
    # 입력 박스 (닉네임)
    txt_surface = font.render(text, True, color)
    width = max(260, txt_surface.get_width()+10)
    input_box.w = width
    screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
    pygame.draw.rect(screen, color, input_box, 2)
    # 입력 박스 (비밀번호)
    pw_surface = font.render('*'*len(password), True, color_pw)
    width_pw = max(260, pw_surface.get_width()+10)
    input_box_pw.w = width_pw
    screen.blit(pw_surface, (input_box_pw.x+5, input_box_pw.y+5))
    pygame.draw.rect(screen, color_pw, input_box_pw, 2)
    # 안내 텍스트
    label = font.render('닉네임', True, (200, 200, 200))
    screen.blit(label, (350, 170))
    label_pw = font.render('비밀번호', True, (200, 200, 200))
    screen.blit(label_pw, (350, 240))
    mode_label = font.render('로그인' if login_mode=='login' else '회원가입', True, (255,255,0))
    screen.blit(mode_label, (350, 100))
    tab_label = font.render('Tab: 로그인/회원가입 전환', True, (120,120,120))
    screen.blit(tab_label, (350, 60))
    # 결과 메시지
    if msg:
        msg_label = font.render(msg, True, (0,255,0) if '성공' in msg else (255,0,0))
        screen.blit(msg_label, (350, 340))
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
client_socket.close() 