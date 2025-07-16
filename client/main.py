import pygame
import socket
import sys

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

# 서버 연결
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
except Exception as e:
    print('서버 연결 실패:', e)
    sys.exit()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_box.collidepoint(event.pos):
                active = not active
            else:
                active = False
            color = color_active if active else color_inactive
        if event.type == pygame.KEYDOWN:
            if active:
                if event.key == pygame.K_RETURN:
                    # 서버로 로그인 요청
                    client_socket.sendall(f'LOGIN:{text}'.encode())
                    text = ''
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

    screen.fill((30, 30, 50))
    # 입력 박스
    txt_surface = font.render(text, True, color)
    width = max(260, txt_surface.get_width()+10)
    input_box.w = width
    screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
    pygame.draw.rect(screen, color, input_box, 2)
    # 안내 텍스트
    label = font.render('닉네임을 입력하세요', True, (200, 200, 200))
    screen.blit(label, (350, 150))
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
client_socket.close() 