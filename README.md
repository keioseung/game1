# Python MMORPG 프로젝트 (Demo)

## 개요
- 파이썬(Python)과 Pygame, socket을 활용한 2D MMORPG 데모 프로젝트입니다.
- 클라이언트/서버 구조로, 로그인, 맵 이동, 채팅, 몬스터 전투, 인벤토리 등 MMORPG의 핵심 기능을 포함합니다.
- 고급스러운 UI와 구조화된 코드, 샘플 리소스를 제공합니다.

## 실행 방법
1. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
2. 서버 실행
   ```bash
   python server/main.py
   ```
3. 클라이언트 실행 (새 터미널에서)
   ```bash
   python client/main.py
   ```

## 주요 폴더 구조
```
project_root/
├── client/         # 클라이언트 코드 (Pygame 기반)
├── server/         # 서버 코드 (socket 기반)
├── resources/      # 이미지, 사운드 등 리소스
├── requirements.txt
└── README.md
```

## 주요 기능
- 회원가입/로그인 (로컬 DB)
- 실시간 맵 이동, 캐릭터 이동
- 몬스터 스폰 및 전투
- 채팅 시스템
- 인벤토리/아이템 획득
- 고급스러운 UI/이펙트

## 참고
- 본 프로젝트는 데모/샘플용으로, 실제 상용화에는 추가 보안 및 최적화가 필요합니다. 