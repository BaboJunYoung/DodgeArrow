# p1_game_refactored.py (p1.py 기반)
import pygame
import random
import math
import json
from dataclasses import dataclass

# 🎨 상수 정의
# 화면 크기 관련 상수는 통합을 위해 제거했습니다.
FPS = 60
HUD_H = 70

# 🎨 색상 정의
BG_COLOR = (22, 24, 27)
HUD_BG = (30, 32, 38)
FRAME_COLOR = (55, 60, 75)
TEXT_COLOR = (235, 238, 245)
SUB_TEXT = (200, 205, 215)
PLAYER_COLOR = (230, 230, 240)
SHAFT_MAIN = (170, 205, 255)
SHAFT_CORE = (220, 240, 255)
SHAFT_OUTLINE = (70, 105, 165)
HEAD_MAIN = (255, 145, 130)
HEAD_OUTLINE = (210, 90, 80)
COLOR_FEATHER_OUT = (80, 110, 175)
COLOR_FEATHER = (170, 205, 255)

# 🏹 게임 파라미터
ARROW_LENGTH = 150
ARROW_SHAFT_W = 7
ARROW_HEAD_LEN = 26
ARROW_HEAD_W = 18
ARROW_FEATHER_LEN = 18
ARROW_FEATHER_W = 14
PLAYER_RADIUS = 16
PLAYER_SPEED = 5.0
ARROW_MIN_SPEED = 3.0
ARROW_MAX_SPEED = 6.0
ARROW_SPAWN_INTERVAL_INIT = 800
ARROW_SPAWN_INTERVAL_MIN = 260
ARROW_SPAWN_ACCEL_EVERY = 12
SHAFT_SCORE_COOLDOWN_MS = 450
SCORE_PER_SHAFT = 1
SKILL_METER_MAX = 15
SKILL_DURATION_MS = 7000
SLOW_FACTOR = 0.25
SHOW_HITBOX = False


# 🛠️ 헬퍼 함수
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def vec_normalize(x, y):
    mag = math.hypot(x, y)
    if mag == 0:
        return 0, 0
    return x / mag, y / mag


@dataclass
class SkillState:
    meter: int = 0
    ready: bool = False
    
    # 통합 환경에서 사용 가능하도록, who 인수를 추가하여 1P/2P 구분이 쉽도록 했습니다.
    def add(self, amount: int, who: str = "1P"):
        if self.ready:
            return
        self.meter += amount
        if self.meter >= SKILL_METER_MAX:
            self.meter = SKILL_METER_MAX
            self.ready = True
            try:
                # JSON 파일 이름을 who에 따라 변경하여 충돌 방지
                filename = f"skill_state_{who}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(
                        {"skill_ready": True, "who": who, "timestamp": pygame.time.get_ticks()},
                        f,
                        ensure_ascii=False
                    )
            except Exception:
                pass

    def consume(self):
        if self.ready:
            self.ready = False
            self.meter = 0


class Player:
    def __init__(self, x, y, bounds_rect: pygame.Rect):
        self.x = x
        self.y = y
        self.r = PLAYER_RADIUS
        self.base_speed = PLAYER_SPEED
        self.speed = self.base_speed
        self.bounds = bounds_rect

    # ... (handle_input, circle, draw 메서드는 그대로 유지)
    def handle_input(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1
        if dx or dy:
            dx, dy = vec_normalize(dx, dy)

        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = clamp(self.x, self.bounds.left + self.r, self.bounds.right - self.r)
        self.y = clamp(self.y, self.bounds.top + self.r, self.bounds.bottom - self.r)

    def circle(self):
        return pygame.math.Vector2(self.x, self.y), self.r

    def draw(self, surf):
        pygame.draw.circle(surf, PLAYER_COLOR, (int(self.x), int(self.y)), self.r)


class Arrow:
    def __init__(self, origin, velocity):
        self.x, self.y = origin
        vx, vy = vec_normalize(*velocity)
        base_speed = random.uniform(ARROW_MIN_SPEED, ARROW_MAX_SPEED)
        self.vx = vx * base_speed
        self.vy = vy * base_speed
        self.last_scored_time = -99999
        base_angle_deg = math.degrees(math.atan2(self.vy, self.vx))
        self.image, self.rect, self.shaft_mask, self.head_mask = self._build_surface(base_angle_deg)

    # ... (_build_surface, update, draw, offscreen, check_collision 메서드는 그대로 유지)
    def _build_surface(self, angle_deg):
        total_len = ARROW_LENGTH + ARROW_HEAD_LEN + 20
        surf_w = total_len
        surf_h = max(ARROW_HEAD_W, ARROW_FEATHER_W) + 30
        shaft_layer = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        head_layer = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        cx, cy = 18, surf_h // 2
        tail_x = cx - 6
        f1 = [(tail_x, cy), (tail_x - ARROW_FEATHER_LEN, cy - ARROW_FEATHER_W), (tail_x - ARROW_FEATHER_LEN * 0.4, cy - ARROW_FEATHER_W * 0.3)]
        f2 = [(tail_x, cy), (tail_x - ARROW_FEATHER_LEN, cy + ARROW_FEATHER_W), (tail_x - ARROW_FEATHER_LEN * 0.4, cy + ARROW_FEATHER_W * 0.3)]
        for pts in (f1, f2):
            pygame.draw.polygon(shaft_layer, COLOR_FEATHER_OUT, pts)
            shrink = [(x + (cx - x) * 0.15, y + (cy - y) * 0.15) for x, y in pts]
            pygame.draw.polygon(shaft_layer, COLOR_FEATHER, shrink)
        outer_rect = pygame.Rect(cx, cy - ARROW_SHAFT_W // 2 - 1, ARROW_LENGTH, ARROW_SHAFT_W + 2)
        pygame.draw.rect(shaft_layer, SHAFT_OUTLINE, outer_rect, border_radius=4)
        main_rect = pygame.Rect(cx, cy - ARROW_SHAFT_W // 2, ARROW_LENGTH, ARROW_SHAFT_W)
        pygame.draw.rect(shaft_layer, SHAFT_MAIN, main_rect, border_radius=4)
        inner_rect = pygame.Rect(cx, cy - ARROW_SHAFT_W // 4, ARROW_LENGTH, ARROW_SHAFT_W // 2)
        pygame.draw.rect(shaft_layer, SHAFT_CORE, inner_rect, border_radius=3)
        tip_x = cx + ARROW_LENGTH
        half_w = ARROW_HEAD_W // 2
        outline_pts = [(tip_x + 3, cy), (tip_x - ARROW_HEAD_LEN, cy - half_w - 2), (tip_x - ARROW_HEAD_LEN, cy + half_w + 2)]
        inner_pts = [(tip_x + 1, cy), (tip_x - ARROW_HEAD_LEN + 4, cy - half_w + 1), (tip_x - ARROW_HEAD_LEN + 4, cy + half_w - 1)]
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

    def update(self, speed_factor: float = 1.0):
        self.x += self.vx * speed_factor
        self.y += self.vy * speed_factor
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf):
        surf.blit(self.image, self.rect)
        if SHOW_HITBOX:
            pygame.draw.rect(surf, (80, 180, 90), self.rect, 1)

    def offscreen(self, play_rect: pygame.Rect):
        pad = 120
        return (self.x < play_rect.left - pad or self.x > play_rect.right + pad or
                self.y < play_rect.top - pad or self.y > play_rect.bottom + pad)

    def check_collision(self, player_pos, player_radius, now_ms):
        px, py = int(player_pos[0]), int(player_pos[1])
        rpad = player_radius + 4
        p_surf = pygame.Surface((rpad * 2, rpad * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (255, 255, 255), (rpad, rpad), player_radius)
        p_mask = pygame.mask.from_surface(p_surf)
        p_rect = p_surf.get_rect(center=(px, py))

        offset_head = (p_rect.left - self.rect.left, p_rect.top - self.rect.top)
        if self.head_mask.overlap(p_mask, offset_head):
            return True, 0

        offset_shaft = (p_rect.left - self.rect.left, p_rect.top - self.rect.top)
        if self.shaft_mask.overlap(p_mask, offset_shaft):
            if now_ms - self.last_scored_time >= SHAFT_SCORE_COOLDOWN_MS:
                self.last_scored_time = now_ms
                return False, SCORE_PER_SHAFT

        return False, 0


class SlashEffect:
    # ... (SlashEffect 클래스는 그대로 유지)
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
    # ... (Spawner 클래스는 그대로 유지)
    def __init__(self, play_rect: pygame.Rect):
        self.interval = ARROW_SPAWN_INTERVAL_INIT
        self.spawned = 0
        self.last_spawn = 0
        self.play_rect = play_rect

    def maybe_spawn(self, now_ms, target_pos):
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

        tx = target_pos[0] + random.uniform(-80, 80)
        ty = target_pos[1] + random.uniform(-80, 80)
        return Arrow((x, y), (tx - x, ty - y))


# 🎨 HUD 그리기 함수 수정: W, H_HUD 인수를 받도록 변경하여 유연성 확보
def draw_hud(surf, score, skill: SkillState, slow_active, slow_remain_ms, W, H_HUD):
    pygame.draw.rect(surf, HUD_BG, pygame.Rect(0, 0, W, H_HUD))
    pygame.draw.line(surf, FRAME_COLOR, (0, H_HUD), (W, H_HUD), 2)

    title_font = pygame.font.SysFont("malgungothic", 26, bold=True)
    small_font = pygame.font.SysFont("malgungothic", 20)

    title = title_font.render("1P", True, TEXT_COLOR)
    surf.blit(title, (20, 18))

    score_s = small_font.render(f"Score : {score}", True, TEXT_COLOR)
    surf.blit(score_s, (80, 20))

    bar_x, bar_y, bar_w, bar_h = 260, 24, 260, 12
    pygame.draw.rect(surf, (65, 70, 82), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
    ratio = skill.meter / SKILL_METER_MAX
    pygame.draw.rect(
        surf,
        (120, 210, 255),
        (bar_x, bar_y, int(bar_w * ratio), bar_h),
        border_radius=6
    )

    if slow_active:
        sec = slow_remain_ms / 1000.0
        # W를 기준으로 중앙 정렬하거나 오른쪽 끝에 위치시키는 로직 추가 가능
        timer_text = small_font.render(f"Skill : {sec:.1f}s", True, SUB_TEXT)
        surf.blit(timer_text, (bar_x + bar_w + 20, 20))


def main():
    # WIDTH, HEIGHT 전역 변수 대신 이 함수 내부에서 정의
    W, H = 1100, 700 
    
    global SHOW_HITBOX
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("죽림 고수 1P")
    clock = pygame.time.Clock()

    # play_rect 정의 시 W, H 사용
    play_rect = pygame.Rect(0, HUD_H, W, H - HUD_H)

    running_global = True
    while running_global:
        player = Player(play_rect.centerx, play_rect.centery, play_rect)
        arrows = []
        effects = []
        spawner = Spawner(play_rect)
        score = 0
        skill = SkillState()

        slow_active = False
        slow_end_time = 0
        dead = False

        while not dead:
            dt = clock.tick(FPS)
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_global = False
                    dead = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running_global = False
                        dead = True
                    if event.key == pygame.K_h:
                        SHOW_HITBOX = not SHOW_HITBOX
                    if event.key == pygame.K_e and skill.ready and not slow_active:
                        skill.consume()
                        slow_active = True
                        slow_end_time = now + SKILL_DURATION_MS
                        player.speed = player.base_speed * 1.5

            if not running_global:
                break

            if slow_active and now >= slow_end_time:
                slow_active = False
                player.speed = player.base_speed

            speed_factor = SLOW_FACTOR if slow_active else 1.0

            spawn = spawner.maybe_spawn(now, (player.x, player.y))
            if spawn:
                arrows.append(spawn)

            player.handle_input()
            for a in arrows:
                a.update(speed_factor)

            for ef in effects:
                ef.update()
            effects = [e for e in effects if e.alive]

            player_pos, player_r = player.circle()
            gained = 0
            arrows_to_remove = []

            for a in arrows:
                hit_head, plus = a.check_collision(player_pos, player_r, now)
                if hit_head:
                    dead = True
                    break
                if plus > 0:
                    gained += plus
                    arrows_to_remove.append(a)
                    effects.append(SlashEffect(a.rect.center))

            if gained:
                score += gained
                skill.add(gained)

            arrows = [
                a for a in arrows
                if (a not in arrows_to_remove) and (not a.offscreen(play_rect))
            ]

            screen.fill(BG_COLOR)
            pygame.draw.rect(screen, (18, 20, 24), play_rect)
            pygame.draw.rect(screen, FRAME_COLOR, play_rect, 2)

            for a in arrows:
                a.draw(screen)
            for ef in effects:
                ef.draw(screen)
            player.draw(screen)

            remain_ms = max(0, slow_end_time - now) if slow_active else 0
            # draw_hud 호출 시 W, HUD_H 전달
            draw_hud(screen, score, skill, slow_active, remain_ms, W, HUD_H)
            pygame.display.flip()

        if not running_global:
            break

    pygame.quit()


if __name__ == "__main__":
    main()