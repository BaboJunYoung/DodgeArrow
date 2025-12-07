import pygame
import random
import math
import sys

# =========================
#  기본 초기화
# =========================
pygame.init()
try:
    pygame.font.init()
except:
    pass

# =========================
#  화면 / 전투 구역 설정
# =========================
F_W, F_H = 1200, 700          # 전체 창 크기
FIGHT_H = 350                 # 위쪽 전투 구역 높이
PLAY_H = F_H - FIGHT_H        # 아래쪽 플레이 구역 높이

screen = pygame.display.set_mode((F_W, F_H), pygame.RESIZABLE)
pygame.display.set_caption("DodgeArrow")
clock = pygame.time.Clock()
FPS = 60

WIN_SCORE_THRESHOLD = 50      # 합산 점수 이 이상이면 승리

# =========================
#  캐릭터 / 보스 스케일 & 발 위치
# =========================
CHAR_SCALE = 1.1              # 플레이어 크기
BOSS_SCALE = 1.8              # 보스 크기

# 전투 구역에서 "지면"이 되는 기준 (위에서 얼마나 띄울지)
FIGHT_GROUND_OFFSET = 100

# 1P 무적 옵션 (테스트용)
INVINCIBLE_1P = False         # True로 두면 1P는 머리에 맞아도 안 죽음

# =========================
#  유틸 함수
# =========================
def load_image(path: str):
    return pygame.image.load(path).convert_alpha()

def scale_image(img: pygame.Surface, scale: float):
    w = int(img.get_width() * scale)
    h = int(img.get_height() * scale)
    return pygame.transform.scale(img, (w, h))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def vec_normalize(x, y):
    mag = math.hypot(x, y)
    if mag == 0:
        return 0, 0
    return x / mag, y / mag

# =========================
#  에셋 로딩
# =========================

# --- 배경 ---
backgroundOriginal = load_image("./assets/background.png")  # 원본 유지
backgroundImage = None  # 실제로 그릴 때 쓰는 배경 (리사이즈 후)

# --- 캐릭터 ---
# 가정: player/1 = 활, player/2 = 검
# 1P = 검, 2P = 활
p1_idle_raw = load_image("./assets/player/2/idle.png")                    # 검
p1_attack_raw = [load_image(f"./assets/player/2/attack{i}.png") for i in range(2)]

p2_idle_raw = load_image("./assets/player/1/idle.png")                    # 활
p2_attack_raw = [load_image(f"./assets/player/1/attack{i}.png") for i in range(2)]

# ★ 방향 바꾸고 싶으면 여기만 수정하면 됨 ★
FLIP_P1 = True   # 1P 좌우 반전 여부 (True면 좌우 반전)
FLIP_P2 = True   # 2P 좌우 반전 여부

# 스케일 먼저
p1_idle_scaled = scale_image(p1_idle_raw, CHAR_SCALE)
p1_attack_scaled = [scale_image(img, CHAR_SCALE) for img in p1_attack_raw]

p2_idle_scaled = scale_image(p2_idle_raw, CHAR_SCALE)
p2_attack_scaled = [scale_image(img, CHAR_SCALE) for img in p2_attack_raw]

# 플래그에 따라 방향 적용
if FLIP_P1:
    char1Idle = pygame.transform.flip(p1_idle_scaled, True, False)
    char1Attack = [pygame.transform.flip(img, True, False) for img in p1_attack_scaled]
else:
    char1Idle = p1_idle_scaled
    char1Attack = p1_attack_scaled

if FLIP_P2:
    char2Idle = pygame.transform.flip(p2_idle_scaled, True, False)
    char2Attack = [pygame.transform.flip(img, True, False) for img in p2_attack_scaled]
else:
    char2Idle = p2_idle_scaled
    char2Attack = p2_attack_scaled

# --- 보스 ---
boss_idle_raw = load_image("./assets/boss/idle.png")
boss_idle_scaled = scale_image(boss_idle_raw, BOSS_SCALE)

boss_attack_raw = [load_image(f"./assets/boss/attack{i}.png") for i in range(3)]
boss_attack_scaled = [scale_image(img, BOSS_SCALE) for img in boss_attack_raw]

bossIdle = boss_idle_scaled
bossHit = boss_attack_scaled

# =========================
#  전투 구역(위쪽) 애니메이션 상태
# =========================
isAttackingChar1 = False
currentFrameChar1 = 0
animationCounterChar1 = 0

isAttackingChar2 = False
currentFrameChar2 = 0
animationCounterChar2 = 0

bossFrame = 0
bossAnimationCounter = 0

charAnimationSpeed = 8
bossAnimationSpeed = 10

FIGHT_ATTACK_1P_THRESHOLD = 5
FIGHT_ATTACK_2P_THRESHOLD = 5

# 캐릭터 / 보스 위치(왼쪽 위 좌표)
char1Pos = (0, 0)
char2Pos = (0, 0)
bossPos = (0, 0)

def setCharacterPosition(current_F_W, current_FIGHT_H):
    """
    창 크기 바뀔 때마다:
    - 전투 배경 스케일
    - 1P / 2P / 보스를 같은 '지면' 기준으로 배치
    """
    global backgroundImage, char1Pos, bossPos, char2Pos

    # 배경 스케일 (항상 원본에서)
    backgroundImage = pygame.transform.scale(
        backgroundOriginal, (current_F_W, current_FIGHT_H)
    )

    # 지면 y 위치 (발 닿는 곳)
    ground_y = current_FIGHT_H - FIGHT_GROUND_OFFSET

    # x 위치 (비율 기반)
    char1_x = current_F_W * 0.75 // 4
    boss_x  = current_F_W * 2 // 4
    char2_x = current_F_W * 3.3 // 4

    # 이미지 크기
    c1_w, c1_h = char1Idle.get_size()
    c2_w, c2_h = char2Idle.get_size()
    b_w,  b_h  = bossIdle.get_size()

    # 발바닥이 ground_y에 닿도록
    char1_y = ground_y - c1_h
    char2_y = ground_y - c2_h

    # 보스는 약간 더 아래에서 서 있게 조정
    boss_ground_y = ground_y + 10
    boss_y = boss_ground_y - b_h

    char1Pos = (char1_x - c1_w // 2, char1_y)
    bossPos  = (boss_x  - b_w  // 2, boss_y)
    char2Pos = (char2_x - c2_w // 2, char2_y)

# 처음 한 번 위치 세팅
setCharacterPosition(F_W, FIGHT_H)

def draw_fight_scene(surf):
    """위쪽 전투 구역 그리기"""
    global isAttackingChar1, currentFrameChar1, animationCounterChar1, \
        isAttackingChar2, currentFrameChar2, animationCounterChar2, \
        bossFrame, bossAnimationCounter

    surf.blit(backgroundImage, (0, 0))

    # 보스 이미지 선택
    if isAttackingChar1 or isAttackingChar2:
        currentBossImage = bossHit[bossFrame]
    else:
        currentBossImage = bossIdle

    # 1P, 2P 이미지 선택
    currentPlayer1Image = char1Attack[currentFrameChar1] if isAttackingChar1 else char1Idle
    currentPlayer2Image = char2Attack[currentFrameChar2] if isAttackingChar2 else char2Idle

    # 그리기
    surf.blit(currentPlayer1Image, char1Pos)
    surf.blit(currentBossImage, bossPos)
    surf.blit(currentPlayer2Image, char2Pos)

def update_fight_animation():
    """위쪽 전투 애니메이션 프레임 진행"""
    global isAttackingChar1, currentFrameChar1, animationCounterChar1, \
        isAttackingChar2, currentFrameChar2, animationCounterChar2, \
        bossFrame, bossAnimationCounter

    # 1P
    if isAttackingChar1:
        animationCounterChar1 += 1
        if animationCounterChar1 >= charAnimationSpeed:
            currentFrameChar1 += 1
            animationCounterChar1 = 0
            if currentFrameChar1 >= len(char1Attack):
                isAttackingChar1 = False
                currentFrameChar1 = 0

    # 2P
    if isAttackingChar2:
        animationCounterChar2 += 1
        if animationCounterChar2 >= charAnimationSpeed:
            currentFrameChar2 += 1
            animationCounterChar2 = 0
            if currentFrameChar2 >= len(char2Attack):
                isAttackingChar2 = False
                currentFrameChar2 = 0

    # 보스
    if isAttackingChar1 or isAttackingChar2:
        bossAnimationCounter += 1
        if bossAnimationCounter >= bossAnimationSpeed:
            bossFrame += 1
            bossAnimationCounter = 0
            if bossFrame >= len(bossHit):
                bossFrame = 0
    else:
        bossFrame = 0
        bossAnimationCounter = 0

last_attack_score_1p = 0
last_attack_score_2p = 0

def try_fight_attack(current_score_1p, current_score_2p):
    """점수에 따라 위쪽 캐릭터 공격 애니메이션 트리거"""
    global isAttackingChar1, isAttackingChar2, last_attack_score_1p, last_attack_score_2p

    if current_score_1p >= last_attack_score_1p + FIGHT_ATTACK_1P_THRESHOLD:
        if not isAttackingChar1:
            isAttackingChar1 = True
            last_attack_score_1p = current_score_1p

    if current_score_2p >= last_attack_score_2p + FIGHT_ATTACK_2P_THRESHOLD:
        if not isAttackingChar2:
            isAttackingChar2 = True
            last_attack_score_2p = current_score_2p

# =========================
#  아래 플레이 구역 설정 상수
# =========================
W, H = F_W, PLAY_H
HUD_H = 70
CENTER_X = W // 2

BG_COLOR = (22, 24, 27)
HUD_BG = (30, 32, 38)
FRAME_COLOR = (55, 60, 75)
TEXT_COLOR = (235, 238, 245)

PLAYER_COLOR_1P = (100, 150, 255)
PLAYER_COLOR_2P = (255, 100, 150)

SHAFT_MAIN = (170, 205, 255)
SHAFT_CORE = (220, 240, 255)
SHAFT_OUTLINE = (70, 105, 165)
HEAD_MAIN = (255, 145, 130)
HEAD_OUTLINE = (210, 90, 80)
COLOR_FEATHER_OUT = (80, 110, 175)
COLOR_FEATHER = (170, 205, 255)

COLOR_FEATHER = (170, 205, 255)

# ===== Devil Arrow Sprite =====
# 파일 이름이 'boss_arrow.png.png'면 아래 그대로 두고,
# 'boss_arrow.png'로 이름을 바꿨다면 이 경로도 같이 바꿔 주세요.
DEVIL_ARROW_IMG = pygame.image.load("assets/boss_arrow.png").convert_alpha()

# 게임 화면에 맞게 크기 조절 (원본이 너무 크면 숫자를 줄이세요)
DEVIL_ARROW_IMG = pygame.transform.smoothscale(DEVIL_ARROW_IMG, (110, 110))

# 원본이 대각선(왼쪽 아래 -> 오른쪽 위) 방향이라
# 기준 방향을 "오른쪽"으로 맞춰두고, 실제 각도에 맞게 다시 회전해서 씁니다.
# 화살 이미지 기본 회전값을 오른쪽 방향 기준으로 맞춘 버전

DEVIL_ARROW_BASE = pygame.transform.rotate(DEVIL_ARROW_IMG, -45)



ARROW_FEATHER_LEN = 12
ARROW_FEATHER_W = 10
ARROW_LENGTH = 105
ARROW_SHAFT_W = 5
ARROW_HEAD_LEN = 18
ARROW_HEAD_W = 12

PLAYER_RADIUS = 16
PLAYER_RADIUS_SMALL = 9
PLAYER_SPEED = 5.0

ARROW_MIN_SPEED = 3.0
ARROW_MAX_SPEED = 6.0
ARROW_SPAWN_INTERVAL_INIT = 800
ARROW_SPAWN_INTERVAL_MIN = 260
ARROW_SPAWN_ACCEL_EVERY = 12

SHAFT_SCORE_COOLDOWN_MS = 450
SCORE_PER_SHAFT = 1

SKILL_METER_MAX_1P = 15
SKILL_METER_MAX_2P = 20
SKILL_DURATION_MS_1P = 7000
SKILL_DURATION_MS_2P = 10000
SLOW_FACTOR = 0.25

PROX_DIST_1 = 120
PROX_DIST_2 = 85
PROX_DIST_3 = 55

SHOW_HITBOX = False
BOUNDARY_BUFFER = 50
GAME_OVER_DELAY_MS = 2000

# 2P 보호막: 스킬 쓰고 이 시간 동안 머리에 맞으면 한 번 막아줌
SHIELD_DURATION_MS_2P = 5000
SHIELD_ACTIVE_DRAW = False   # 그릴 때 노란 테두리 표시용

# =========================
#  클래스들
# =========================
class SkillState:
    def __init__(self, who: str):
        self.who = who
        self.meter = 0
        self.ready = False
        self.max_meter = SKILL_METER_MAX_1P if who == "1P" else SKILL_METER_MAX_2P

    def add(self, amount: int):
        if self.ready:
            return
        self.meter += amount
        if self.meter >= self.max_meter:
            self.meter = self.max_meter
            self.ready = True

    def consume(self):
        if self.ready:
            self.ready = False
            self.meter = 0

class Player:
    def __init__(self, x, y, bounds_rect: pygame.Rect, who: str):
        self.x = x
        self.y = y
        self.who = who
        self.bounds = bounds_rect
        self.base_speed = PLAYER_SPEED
        self.speed = self.base_speed
        self.base_r = PLAYER_RADIUS
        self.small_r = PLAYER_RADIUS_SMALL
        self.r = self.base_r
        self.color = PLAYER_COLOR_1P if who == "1P" else PLAYER_COLOR_2P

    def handle_input(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0

        if self.who == "1P":
            if keys[pygame.K_w]: dy -= 1
            if keys[pygame.K_s]: dy += 1
            if keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_d]: dx += 1
        elif self.who == "2P":
            if keys[pygame.K_UP]: dy -= 1
            if keys[pygame.K_DOWN]: dy += 1
            if keys[pygame.K_LEFT]: dx -= 1
            if keys[pygame.K_RIGHT]: dx += 1

        if dx or dy:
            dx, dy = vec_normalize(dx, dy)

        self.x += dx * self.speed
        self.y += dy * self.speed

        self.x = clamp(self.x, self.bounds.left + self.r, self.bounds.right - self.r)
        self.y = clamp(self.y, self.bounds.top + self.r, self.bounds.bottom - self.r)

    def set_speed_factor(self, factor: float):
        self.speed = self.base_speed * factor

    def set_small(self, small: bool):
        if self.who == "2P":
            self.r = self.small_r if small else self.base_r
            self.x = clamp(self.x, self.bounds.left + self.r, self.bounds.right - self.r)
            self.y = clamp(self.y, self.bounds.top + self.r, self.bounds.bottom - self.r)

    def circle(self):
        return pygame.math.Vector2(self.x, self.y), self.r

    def draw(self, surf):
        global SHIELD_ACTIVE_DRAW
        center = (int(self.x), int(self.y))
        pygame.draw.circle(surf, self.color, center, self.r)

        if self.who == "2P" and self.r == self.small_r:
            # 작아졌을 때 기본 흰색 테두리
            pygame.draw.circle(surf, (255, 255, 255), center, self.r, 2)
            # 보호막 켜져 있으면 노란 테두리
            if SHIELD_ACTIVE_DRAW:
                pygame.draw.circle(surf, (255, 230, 80), center, self.r + 3, 2)

class Arrow:
    def __init__(self, origin, velocity):
        self.x, self.y = origin
        vx, vy = vec_normalize(*velocity)
        base_speed = random.uniform(ARROW_MIN_SPEED, ARROW_MAX_SPEED)
        self.vx = vx * base_speed
        self.vy = vy * base_speed
        self.dirx = vx
        self.diry = vy
        self.last_scored_time = -99999
        self.head_offset = ARROW_LENGTH * 0.45 + ARROW_HEAD_LEN * 0.5
        self.proximity_level = 0
        base_angle_deg = math.degrees(math.atan2(self.vy, self.vx))
        self.angle_deg = base_angle_deg  # 스프라이트 회전용 각도
        self.image, self.rect, self.shaft_mask, self.head_mask = self._build_surface(base_angle_deg)


    def _build_surface(self, angle_deg):
        total_len = ARROW_LENGTH + ARROW_HEAD_LEN + 20
        surf_w = total_len
        surf_h = max(ARROW_HEAD_W, ARROW_FEATHER_W) + 30
        shaft_layer = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        head_layer = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

        cx, cy = 18, surf_h // 2
        tail_x = cx - 6

        # 깃털
        f1 = [(tail_x, cy), (tail_x - ARROW_FEATHER_LEN, cy - ARROW_FEATHER_W),
              (tail_x - ARROW_FEATHER_LEN * 0.4, cy - ARROW_FEATHER_W * 0.3)]
        f2 = [(tail_x, cy), (tail_x - ARROW_FEATHER_LEN, cy + ARROW_FEATHER_W),
              (tail_x - ARROW_FEATHER_LEN * 0.4, cy + ARROW_FEATHER_W * 0.3)]
        for pts in (f1, f2):
            pygame.draw.polygon(shaft_layer, COLOR_FEATHER_OUT, pts)
            shrink = [(x + (cx - x) * 0.15, y + (cy - y) * 0.15) for x, y in pts]
            pygame.draw.polygon(shaft_layer, COLOR_FEATHER, shrink)

        # 몸통
        outer_rect = pygame.Rect(cx, cy - ARROW_SHAFT_W // 2 - 1, ARROW_LENGTH, ARROW_SHAFT_W + 2)
        pygame.draw.rect(shaft_layer, SHAFT_OUTLINE, outer_rect, border_radius=4)
        main_rect = pygame.Rect(cx, cy - ARROW_SHAFT_W // 2, ARROW_LENGTH, ARROW_SHAFT_W)
        pygame.draw.rect(shaft_layer, SHAFT_MAIN, main_rect, border_radius=4)
        inner_rect = pygame.Rect(cx, cy - ARROW_SHAFT_W // 4, ARROW_LENGTH, ARROW_SHAFT_W // 2)
        pygame.draw.rect(shaft_layer, SHAFT_CORE, inner_rect, border_radius=3)

        # 화살촉
        tip_x = cx + ARROW_LENGTH
        half_w = ARROW_HEAD_W // 2
        outline_pts = [(tip_x + 3, cy), (tip_x - ARROW_HEAD_LEN, cy - half_w - 2),
                       (tip_x - ARROW_HEAD_LEN, cy + half_w + 2)]
        inner_pts = [(tip_x + 1, cy), (tip_x - ARROW_HEAD_LEN + 4, cy - half_w + 1),
                     (tip_x - ARROW_HEAD_LEN + 4, cy + half_w - 1)]
        pygame.draw.polygon(head_layer, HEAD_OUTLINE, outline_pts)
        pygame.draw.polygon(head_layer, HEAD_MAIN, inner_pts)

        shaft_img = pygame.transform.rotate(shaft_layer, -angle_deg)
        head_img = pygame.transform.rotate(head_layer, -angle_deg)

        final_w = max(shaft_img.get_width(), head_img.get_width())
        final_h = max(shaft_img.get_height(), head_img.get_height())
        final_img = pygame.Surface((final_w, final_h), pygame.SRCALPHA)

        shaft_rect = shaft_img.get_rect(center=(final_w // 2, final_h // 2))
        head_rect = head_img.get_rect(center=(final_w // 2, final_h // 2))

        final_img.blit(shaft_img, shaft_rect)
        final_img.blit(head_img, head_rect)

        shaft_mask = pygame.mask.from_surface(shaft_img)
        head_mask = pygame.mask.from_surface(head_img)
        rect = final_img.get_rect(center=(int(self.x), int(self.y)))
        return final_img, rect, shaft_mask, head_mask

    def head_pos(self):
        return (
            self.x + self.dirx * self.head_offset,
            self.y + self.diry * self.head_offset
        )

    def update(self, speed_factor: float = 1.0):
        self.x += self.vx * speed_factor
        self.y += self.vy * speed_factor
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf):
        # 악마 화살 스프라이트를 현재 이동 각도에 맞게 회전해서 그립니다.
        # self.rect.center는 기존 충돌 판정용 히트박스의 중심이므로 그대로 사용합니다.
        sprite_img = pygame.transform.rotate(DEVIL_ARROW_BASE, -self.angle_deg+180)
        sprite_rect = sprite_img.get_rect(center=self.rect.center)
        surf.blit(sprite_img, sprite_rect)

        # 디버그용으로 히트박스를 보고 싶으면 SHOW_HITBOX = True로 두세요.
        if SHOW_HITBOX:
            pygame.draw.rect(surf, (80, 180, 90), self.rect, 1)


    def offscreen(self, play_rect: pygame.Rect):
        pad = 120
        return (self.x < play_rect.left - pad or self.x > play_rect.right + pad or
                self.y < play_rect.top - pad or self.y > play_rect.bottom + pad)

    def check_collision(self, player_pos, player_r, now_ms, who: str):
        px, py = int(player_pos[0]), int(player_pos[1])
        rpad = player_r + 4

        p_surf = pygame.Surface((rpad * 2, rpad * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (255, 255, 255), (rpad, rpad), player_r)
        p_mask = pygame.mask.from_surface(p_surf)
        p_rect = p_surf.get_rect(center=(px, py))

        dead = False
        gained = 0
        offset = (p_rect.left - self.rect.left, p_rect.top - self.rect.top)

        # 머리(즉시 사망 판정)
        if self.head_mask.overlap(p_mask, offset):
            dead = True
            return dead, gained, False

        if who == "1P":
            # 1P: 몸통 긁으면 점수
            if self.shaft_mask.overlap(p_mask, offset):
                if now_ms - self.last_scored_time >= SHAFT_SCORE_COOLDOWN_MS:
                    self.last_scored_time = now_ms
                    gained = SCORE_PER_SHAFT
                    return dead, gained, True
            return dead, gained, False

        elif who == "2P":
            # 2P: 몸통 == 즉사 (보호막 여부는 밖에서 처리)
            if self.shaft_mask.overlap(p_mask, offset):
                dead = True
                return dead, gained, False

            # 화살촉 근접도에 따라 점수
            hx, hy = self.head_pos()
            dist = math.hypot(hx - px, hy - py)

            new_level = 0
            if dist <= PROX_DIST_3:
                new_level = 3
            elif dist <= PROX_DIST_2:
                new_level = 2
            elif dist <= PROX_DIST_1:
                new_level = 1

            if new_level > self.proximity_level:
                gained = new_level - self.proximity_level
                self.proximity_level = new_level

            return dead, gained, False

        return dead, gained, False

class SlashEffect:
    def __init__(self, pos):
        self.x, self.y = pos
        self.life = 10
        self.max_life = 10
        self.size = 22
        self.angle = random.uniform(-20, 20)

    @property
    def alive(self):
        return self.life > 0

    def update(self):
        self.life -= 1
        self.size += 2

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        color = (255, 250, 240, alpha)
        length = self.size
        thickness = 3

        temp = pygame.Surface((length * 2, length * 2), pygame.SRCALPHA)
        cx, cy = length, length

        pygame.draw.line(temp, color, (cx - length // 2, cy - length // 2),
                         (cx + length // 2, cy + length // 2), thickness)
        pygame.draw.line(temp, color, (cx - length // 2, cy + length // 2),
                         (cx + length // 2, cy - length // 2), thickness)

        temp = pygame.transform.rotate(temp, self.angle)
        rect = temp.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(temp, rect)

class Spawner:
    def __init__(self, play_rect: pygame.Rect):
        self.interval = ARROW_SPAWN_INTERVAL_INIT
        self.spawned = 0
        self.last_spawn = 0
        self.play_rect = play_rect

    def maybe_spawn(self, now_ms, target_pos_1p, target_pos_2p):
        if now_ms - self.last_spawn < self.interval:
            return None
        self.last_spawn = now_ms
        self.spawned += 1

        if self.spawned % ARROW_SPAWN_ACCEL_EVERY == 0:
            self.interval = max(ARROW_SPAWN_INTERVAL_MIN, int(self.interval * 0.9))

        pr = self.play_rect
        margin = 20
        edge = random.randint(0, 3)

        if edge == 0:
            x = random.randint(pr.left, pr.right)
            y = pr.top - margin
        elif edge == 1:
            x = random.randint(pr.left, pr.right)
            y = pr.bottom + margin
        elif edge == 2:
            x = pr.left - margin
            y = random.randint(pr.top, pr.bottom)
        else:
            x = pr.right + margin
            y = random.randint(pr.top, pr.bottom)

        # 어느 플레이어를 노릴지
        if random.random() < 0.5:
            tx = target_pos_1p[0] + random.uniform(-80, 80)
            ty = target_pos_1p[1] + random.uniform(-80, 80)
        else:
            tx = target_pos_2p[0] + random.uniform(-80, 80)
            ty = target_pos_2p[1] + random.uniform(-80, 80)

        # 중앙 경계 근처에서 바로 넘어오지 않도록 보정
        if pr.left + BOUNDARY_BUFFER < x < pr.right - BOUNDARY_BUFFER:
            pass
        elif x < CENTER_X:
            if CENTER_X - BOUNDARY_BUFFER <= x:
                x = CENTER_X - BOUNDARY_BUFFER - 1
        else:
            if x <= CENTER_X + BOUNDARY_BUFFER:
                x = CENTER_X + BOUNDARY_BUFFER + 1

        # 중앙에 너무 가깝게 생성되면 재귀로 다시 시도
        if CENTER_X - 10 <= x <= CENTER_X + 10:
            return self.maybe_spawn(now_ms, target_pos_1p, target_pos_2p)

        return Arrow((x, y), (tx - x, ty - y))

# =========================
#  HUD / 초기화 / 그리기
# =========================
def draw_hud(surf, score_1p, skill_1p: SkillState, slow_active, slow_remain_ms,
             score_2p, skill_2p: SkillState, small_active, small_remain_ms,
             shield_active):
    pygame.draw.rect(surf, HUD_BG, pygame.Rect(0, 0, W, HUD_H))
    pygame.draw.line(surf, FRAME_COLOR, (0, HUD_H), (W, HUD_H), 2)
    pygame.draw.line(surf, FRAME_COLOR, (CENTER_X, 0), (CENTER_X, HUD_H), 2)

    title_font = pygame.font.SysFont("malgungothic", 26, bold=True)
    small_font = pygame.font.SysFont("malgungothic", 20)

    # 1P HUD
    title_1p = title_font.render("1P", True, PLAYER_COLOR_1P)
    surf.blit(title_1p, (20, 18))
    score_s_1p = small_font.render(f"Score : {score_1p}", True, TEXT_COLOR)
    surf.blit(score_s_1p, (80, 20))

    bar_x_1p, bar_y, bar_w, bar_h = 240, 24, 200, 12
    pygame.draw.rect(surf, (65, 70, 82), (bar_x_1p, bar_y, bar_w, bar_h), border_radius=6)
    ratio_1p = skill_1p.meter / SKILL_METER_MAX_1P
    pygame.draw.rect(surf, (120, 210, 255),
                     (bar_x_1p, bar_y, int(bar_w * ratio_1p), bar_h), border_radius=6)

    if slow_active:
        sec = slow_remain_ms / 1000.0
        timer_text = small_font.render(f"SLOW {sec:.1f}s", True, (120, 210, 255))
        surf.blit(timer_text, (bar_x_1p + bar_w + 20, 20))
    elif skill_1p.ready:
        ready_text = small_font.render("E READY", True, (120, 210, 255))
        surf.blit(ready_text, (bar_x_1p + bar_w + 20, 20))

    # 2P HUD
    offset_x = CENTER_X + 20
    title_2p = title_font.render("2P", True, PLAYER_COLOR_2P)
    surf.blit(title_2p, (offset_x, 18))
    score_s_2p = small_font.render(f"Score : {score_2p}", True, TEXT_COLOR)
    surf.blit(score_s_2p, (offset_x + 60, 20))

    bar_x_2p, bar_y, bar_w, bar_h = offset_x + 220, 24, 200, 12
    pygame.draw.rect(surf, (65, 70, 82), (bar_x_2p, bar_y, bar_w, bar_h), border_radius=6)
    ratio_2p = skill_2p.meter / SKILL_METER_MAX_2P
    pygame.draw.rect(surf, (255, 120, 180),
                     (bar_x_2p, bar_y, int(bar_w * ratio_2p), bar_h), border_radius=6)

    if small_active:
        remain_sec = max(1, small_remain_ms // 1000)
        timer_text = small_font.render(f"SMALL {remain_sec}s", True, (255, 120, 180))
        surf.blit(timer_text, (bar_x_2p + bar_w + 20, 20))
    elif skill_2p.ready:
        ready_text = small_font.render("RSHIFT READY", True, (255, 120, 180))
        surf.blit(ready_text, (bar_x_2p + bar_w + 20, 20))

    if shield_active:
        shield_text = small_font.render("SHIELD", True, (255, 230, 80))
        surf.blit(shield_text, (bar_x_2p + bar_w + 120, 20))

def initialize_play_game():
    """아래 플레이 영역에 필요한 상태들 한 번에 초기화"""
    global last_attack_score_1p, last_attack_score_2p

    play_rect = pygame.Rect(0, HUD_H, W, H - HUD_H)
    play_rect_1p = pygame.Rect(0, HUD_H, CENTER_X, H - HUD_H)
    play_rect_2p = pygame.Rect(CENTER_X, HUD_H, W - CENTER_X, H - HUD_H)

    player_1p = Player(play_rect_1p.centerx, play_rect_1p.centery, play_rect_1p, "1P")
    player_2p = Player(play_rect_2p.centerx, play_rect_2p.centery, play_rect_2p, "2P")
    arrows = []
    effects = []
    spawner = Spawner(play_rect)

    score_1p = 0
    score_2p = 0
    skill_1p = SkillState("1P")
    skill_2p = SkillState("2P")

    slow_active = False
    slow_end_time = 0
    small_active = False
    small_end_time = 0
    shield_active = False
    shield_end_time = 0
    dead_1p = False
    dead_2p = False

    last_attack_score_1p = 0
    last_attack_score_2p = 0

    return (player_1p, player_2p, arrows, effects, spawner,
            score_1p, score_2p,
            skill_1p, skill_2p,
            slow_active, slow_end_time,
            small_active, small_end_time,
            shield_active, shield_end_time,
            dead_1p, dead_2p,
            play_rect, play_rect_1p, play_rect_2p)

def draw_play_scene(surf, play_state):
    """아래쪽 플레이 영역 그리기"""
    global SHIELD_ACTIVE_DRAW

    (player_1p, player_2p, arrows, effects, spawner,
     score_1p, score_2p,
     skill_1p, skill_2p,
     slow_active, slow_end_time,
     small_active, small_end_time,
     shield_active, shield_end_time,
     dead_1p, dead_2p,
     play_rect, play_rect_1p, play_rect_2p) = play_state

    surf.fill(BG_COLOR)
    pygame.draw.rect(surf, (18, 20, 24), pygame.Rect(0, HUD_H, W, H - HUD_H))
    pygame.draw.line(surf, FRAME_COLOR, (CENTER_X, HUD_H), (CENTER_X, H), 3)
    pygame.draw.rect(surf, FRAME_COLOR, pygame.Rect(0, HUD_H, W, H - HUD_H), 2)

    for a in arrows:
        a.draw(surf)
    for ef in effects:
        ef.draw(surf)

    # 2P 플레이어를 그릴 때 보호막 표시 여부
    SHIELD_ACTIVE_DRAW = shield_active

    if not dead_1p:
        player_1p.draw(surf)
    if not dead_2p:
        player_2p.draw(surf)

    now = pygame.time.get_ticks()
    remain_ms_1p = max(0, slow_end_time - now) if slow_active else 0
    remain_ms_2p = max(0, small_end_time - now) if small_active else 0

    draw_hud(surf, score_1p, skill_1p, slow_active, remain_ms_1p,
             score_2p, skill_2p, small_active, remain_ms_2p,
             shield_active)

# =========================
#  메인 루프
# =========================
def main():
    global SHOW_HITBOX, last_attack_score_1p, last_attack_score_2p

    running_global = True

    while running_global:
        play_state = initialize_play_game()
        (player_1p, player_2p, arrows, effects, spawner,
         score_1p, score_2p,
         skill_1p, skill_2p,
         slow_active, slow_end_time,
         small_active, small_end_time,
         shield_active, shield_end_time,
         dead_1p, dead_2p,
         play_rect, play_rect_1p, play_rect_2p) = play_state

        game_over = False
        game_won = False
        last_print_time = 0

        while running_global and not game_over and not game_won:
            dt = clock.tick(FPS)
            now = pygame.time.get_ticks()

            # ------------- 이벤트 처리 -------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_global = False
                    game_over = True

                elif event.type == pygame.VIDEORESIZE:
                    # 창 크기 변경
                    global F_W, F_H, FIGHT_H, PLAY_H, screen, CENTER_X, W, H
                    F_W = event.w
                    F_H = event.h
                    FIGHT_H = F_H * 1 // 2
                    PLAY_H = F_H - FIGHT_H
                    W, H = F_W, PLAY_H
                    CENTER_X = W // 2
                    screen = pygame.display.set_mode((F_W, F_H), pygame.RESIZABLE)

                    # 전투 구역 재배치
                    setCharacterPosition(F_W, FIGHT_H)

                    # 플레이 구역도 초기화
                    (player_1p, player_2p, arrows, effects, spawner,
                     score_1p, score_2p,
                     skill_1p, skill_2p,
                     slow_active, slow_end_time,
                     small_active, small_end_time,
                     shield_active, shield_end_time,
                     dead_1p, dead_2p,
                     play_rect, play_rect_1p, play_rect_2p) = initialize_play_game()
                    play_state = (player_1p, player_2p, arrows, effects, spawner,
                                  score_1p, score_2p,
                                  skill_1p, skill_2p,
                                  slow_active, slow_end_time,
                                  small_active, small_end_time,
                                  shield_active, shield_end_time,
                                  dead_1p, dead_2p,
                                  play_rect, play_rect_1p, play_rect_2p)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running_global = False
                        game_over = True
                    if event.key == pygame.K_h:
                        SHOW_HITBOX = not SHOW_HITBOX

                    # 1P 스킬: E키 -> 전체 슬로우
                    if (not dead_1p and event.key == pygame.K_e and
                            skill_1p.ready and not slow_active):
                        skill_1p.consume()
                        slow_active = True
                        slow_end_time = now + SKILL_DURATION_MS_1P

                    # 2P 스킬: RSHIFT -> 작아지고 + 보호막 1회
                    if (not dead_2p and event.key == pygame.K_RSHIFT and
                            skill_2p.ready and not small_active):
                        skill_2p.consume()
                        small_active = True
                        small_end_time = now + SKILL_DURATION_MS_2P

                        shield_active = True
                        shield_end_time = now + SHIELD_DURATION_MS_2P

            if not running_global:
                break

            # ------------- 상태 업데이트 -------------

            # 전역 슬로우(1P 스킬)
            speed_factor = 1.0
            if slow_active:
                if now >= slow_end_time:
                    slow_active = False
                    player_1p.set_speed_factor(1.0)
                else:
                    speed_factor = SLOW_FACTOR

            # 2P 작은 사이즈 유지 / 종료
            if small_active:
                if now >= small_end_time:
                    small_active = False
                    player_2p.set_small(False)
                else:
                    player_2p.set_small(True)
            elif not dead_2p:
                player_2p.set_small(False)

            # 보호막 시간 끝나면 해제
            if shield_active and now >= shield_end_time:
                shield_active = False

            # 플레이어 이동
            if not dead_1p:
                player_1p.set_speed_factor(1.5 if slow_active else 1.0)
                player_1p.handle_input()
            if not dead_2p:
                player_2p.handle_input()

            # 화살 생성 / 이동
            spawn = spawner.maybe_spawn(now, (player_1p.x, player_1p.y), (player_2p.x, player_2p.y))
            if spawn:
                arrows.append(spawn)

            for a in arrows:
                a.update(speed_factor)

            # slash 이펙트
            for ef in effects:
                ef.update()
            effects = [e for e in effects if e.alive]

            arrows_to_remove = []

            # ---------- 1P 충돌 ----------
            if not dead_1p:
                player_pos_1p, player_r_1p = player_1p.circle()
                gained_1p = 0

                for a in arrows:
                    hit_head, plus, remove = a.check_collision(player_pos_1p, player_r_1p, now, "1P")

                    if (not INVINCIBLE_1P) and hit_head:
                        dead_1p = True
                        break

                    if plus > 0:
                        gained_1p += plus
                        if remove:
                            arrows_to_remove.append(a)
                            effects.append(SlashEffect(a.rect.center))

                if gained_1p:
                    score_1p += gained_1p
                    skill_1p.add(gained_1p)

            # ---------- 2P 충돌 + 보호막 ----------
            if not dead_2p and not dead_1p:
                player_pos_2p, player_r_2p = player_2p.circle()
                gained_2p = 0

                for a in arrows:
                    hit_head, plus, remove = a.check_collision(player_pos_2p, player_r_2p, now, "2P")

                    if hit_head:
                        if shield_active:
                            # 보호막 발동: 화살 삭제 + 이펙트, 보호막 종료
                            arrows_to_remove.append(a)
                            effects.append(SlashEffect(a.rect.center))
                            shield_active = False
                            break
                        else:
                            dead_2p = True
                            break

                    if plus > 0:
                        gained_2p += plus
                        effects.append(SlashEffect((player_pos_2p.x, player_pos_2p.y)))

                if gained_2p:
                    score_2p += gained_2p
                    skill_2p.add(gained_2p)

            # 화면 밖 / 삭제된 화살 제거
            arrows = [
                a for a in arrows
                if (a not in arrows_to_remove) and (not a.offscreen(play_rect))
            ]

            # 사망 / 승리 판정
            if dead_1p or dead_2p:
                game_over = True

            try_fight_attack(score_1p, score_2p)
            update_fight_animation()

            if score_1p + score_2p >= WIN_SCORE_THRESHOLD:
                game_won = True

            # 디버그 출력
            if now - last_print_time > 1000:
                print(f"1P Score: {score_1p} | 2P: {score_2p} | Total: {score_1p + score_2p}")
                last_print_time = now

            # ------------- 실제 그리기 -------------
            screen.fill((0, 0, 0))

            # 위쪽 전투 구역
            fight_surf = screen.subsurface(pygame.Rect(0, 0, F_W, FIGHT_H))
            draw_fight_scene(fight_surf)

            pygame.draw.line(screen, FRAME_COLOR, (0, FIGHT_H), (F_W, FIGHT_H), 5)

            # 아래쪽 플레이 구역
            play_surf = screen.subsurface(pygame.Rect(0, FIGHT_H, F_W, PLAY_H))
            play_state = (player_1p, player_2p, arrows, effects, spawner,
                          score_1p, score_2p,
                          skill_1p, skill_2p,
                          slow_active, slow_end_time,
                          small_active, small_end_time,
                          shield_active, shield_end_time,
                          dead_1p, dead_2p,
                          play_rect, play_rect_1p, play_rect_2p)
            draw_play_scene(play_surf, play_state)

            pygame.display.flip()

        # ------------- 게임 끝 연출 -------------
        if (game_over or game_won) and running_global:
            game_over_font = pygame.font.SysFont("malgungothic", 80, bold=True)
            restart_font = pygame.font.SysFont("malgungothic", 30)

            if game_won:
                go_text = game_over_font.render("VICTORY! YOU WIN!", True, (50, 255, 50))
            elif dead_1p:
                go_text = game_over_font.render("1P DEAD. GAME OVER!", True, PLAYER_COLOR_1P)
            else:
                go_text = game_over_font.render("2P DEAD. GAME OVER!", True, PLAYER_COLOR_2P)

            restart_text = restart_font.render("Restarting...", True, TEXT_COLOR)

            screen.fill(BG_COLOR)
            screen.blit(go_text, go_text.get_rect(center=(F_W // 2, F_H // 2 - 50)))
            screen.blit(restart_text, restart_text.get_rect(center=(F_W // 2, F_H // 2 + 50)))
            pygame.display.flip()

            print("--- GAME END ---")
            if game_won:
                print(f"** VICTORY ** Total Score {score_1p + score_2p} >= {WIN_SCORE_THRESHOLD}")
            else:
                print("** DEFEAT **")
            print(f"FINAL SCORE | 1P: {score_1p} | 2P: {score_2p}")
            print("-----------------")

            pygame.time.delay(GAME_OVER_DELAY_MS)

            # 전투 애니메이션 상태 초기화
            global isAttackingChar1, isAttackingChar2, currentFrameChar1, currentFrameChar2, bossFrame
            isAttackingChar1 = False
            isAttackingChar2 = False
            currentFrameChar1 = 0
            currentFrameChar2 = 0
            bossFrame = 0

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
