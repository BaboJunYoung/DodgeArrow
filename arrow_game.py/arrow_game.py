import pygame
import random
import sys

WIDTH, HEIGHT = 800, 600

class Player:
    def __init__(self):
        self.rect = pygame.Rect(100, HEIGHT // 2, 40, 40)
        self.speed = 5

    def update(self, keys):
        if keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_s]:
            self.rect.y += self.speed
        if keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_d]:
            self.rect.x += self.speed

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
            
            
            
            
#--------------------------------------------------------------------------------------------------------------------------

class Arrow:
    def __init__(self):
        self.head_len = 18
        self.shaft_len = int(42 * 3)
        self.thickness = 16
        self.speed = random.randint(4, 6)

        self.direction = random.choice(["left", "right", "up", "down"])

        total_len = self.head_len + self.shaft_len

        if self.direction in ["left", "right"]:
            w = total_len
            h = self.thickness
            y = random.randint(0, HEIGHT - h)
            if self.direction == "right":
                x = -w
            else:
                x = WIDTH
        else:
            w = self.thickness
            h = total_len
            x = random.randint(0, WIDTH - w)
            if self.direction == "down":
                y = -h
            else:
                y = HEIGHT

        self.rect = pygame.Rect(x, y, w, h)

    def update(self):
        if self.direction == "right":
            self.rect.x += self.speed
        elif self.direction == "left":
            self.rect.x -= self.speed
        elif self.direction == "down":
            self.rect.y += self.speed
        elif self.direction == "up":
            self.rect.y -= self.speed

    def is_off_screen(self):
        return (
            self.rect.right < 0 or
            self.rect.left > WIDTH or
            self.rect.bottom < 0 or
            self.rect.top > HEIGHT
        )

    def head_rect(self):
        if self.direction == "right":
            return pygame.Rect(
                self.rect.x + self.shaft_len,
                self.rect.y,
                self.head_len,
                self.rect.height
            )
        elif self.direction == "left":
            return pygame.Rect(
                self.rect.x,
                self.rect.y,
                self.head_len,
                self.rect.height
            )
        elif self.direction == "down":
            return pygame.Rect(
                self.rect.x,
                self.rect.y + self.shaft_len,
                self.rect.width,
                self.head_len
            )
        else:
            return pygame.Rect(
                self.rect.x,
                self.rect.y,
                self.rect.width,
                self.head_len
            )

    def shaft_rect(self):
        if self.direction == "right":
            return pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height // 4,
                self.shaft_len,
                self.rect.height // 2
            )
        elif self.direction == "left":
            return pygame.Rect(
                self.rect.x + self.head_len,
                self.rect.y + self.rect.height // 4,
                self.shaft_len,
                self.rect.height // 2
            )
        elif self.direction == "down":
            return pygame.Rect(
                self.rect.x + self.rect.width // 4,
                self.rect.y,
                self.rect.width // 2,
                self.shaft_len
            )
        else:
            return pygame.Rect(
                self.rect.x + self.rect.width // 4,
                self.rect.y + self.head_len,
                self.rect.width // 2,
                self.shaft_len
            )

    def draw(self, screen):
        head = self.head_rect()
        shaft = self.shaft_rect()

        wood_color = (181, 140, 64)
        head_color = (210, 210, 210)
        feather_color = (210, 60, 60)

        pygame.draw.rect(screen, wood_color, shaft)

        if self.direction == "right":
            tip = (head.right, head.centery)
            base_top = (head.left, head.top)
            base_bottom = (head.left, head.bottom)
            pygame.draw.polygon(screen, head_color, [base_top, tip, base_bottom])

            tail_width = self.thickness * 1.2
            x0 = shaft.left
            y_top = shaft.top
            y_mid = shaft.centery
            y_bot = shaft.bottom
            pygame.draw.polygon(screen, feather_color, [
                (x0, y_top),
                (x0 - tail_width, y_mid),
                (x0, y_mid)
            ])
            pygame.draw.polygon(screen, feather_color, [
                (x0, y_mid),
                (x0 - tail_width, y_mid),
                (x0, y_bot)
            ])

        elif self.direction == "left":
            tip = (head.left, head.centery)
            base_top = (head.right, head.top)
            base_bottom = (head.right, head.bottom)
            pygame.draw.polygon(screen, head_color, [base_top, tip, base_bottom])

            tail_width = self.thickness * 1.2
            x0 = shaft.right
            y_top = shaft.top
            y_mid = shaft.centery
            y_bot = shaft.bottom
            pygame.draw.polygon(screen, feather_color, [
                (x0, y_top),
                (x0 + tail_width, y_mid),
                (x0, y_mid)
            ])
            pygame.draw.polygon(screen, feather_color, [
                (x0, y_mid),
                (x0 + tail_width, y_mid),
                (x0, y_bot)
            ])

        elif self.direction == "down":
            tip = (head.centerx, head.bottom)
            base_left = (head.left, head.top)
            base_right = (head.right, head.top)
            pygame.draw.polygon(screen, head_color, [base_left, tip, base_right])

            tail_height = self.thickness * 1.2
            y0 = shaft.top
            x_mid = shaft.centerx
            x_left = shaft.left
            x_right = shaft.right
            pygame.draw.polygon(screen, feather_color, [
                (x_left, y0),
                (x_mid, y0 - tail_height),
                (x_mid, y0)
            ])
            pygame.draw.polygon(screen, feather_color, [
                (x_mid, y0),
                (x_mid, y0 - tail_height),
                (x_right, y0)
            ])

        else:
            tip = (head.centerx, head.top)
            base_left = (head.left, head.bottom)
            base_right = (head.right, head.bottom)
            pygame.draw.polygon(screen, head_color, [base_left, tip, base_right])

            tail_height = self.thickness * 1.2
            y0 = shaft.bottom
            x_mid = shaft.centerx
            x_left = shaft.left
            x_right = shaft.right
            pygame.draw.polygon(screen, feather_color, [
                (x_left, y0),
                (x_mid, y0 + tail_height),
                (x_mid, y0)
            ])
            pygame.draw.polygon(screen, feather_color, [
                (x_mid, y0),
                (x_mid, y0 + tail_height),
                (x_right, y0)
            ])


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("사방 화살 게임 - 1P")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    player = Player()
    arrows = []
    score = 0
    game_over = False

    SPAWN_ARROW = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_ARROW, 700)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == SPAWN_ARROW and not game_over:
                arrows.append(Arrow())
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    player = Player()
                    arrows = []
                    score = 0
                    game_over = False

        keys = pygame.key.get_pressed()

        if not game_over:
            player.update(keys)

            for arrow in arrows[:]:
                arrow.update()

                if arrow.is_off_screen():
                    arrows.remove(arrow)
                    continue

                head = arrow.head_rect()
                shaft = arrow.shaft_rect()

                if head.colliderect(player.rect):
                    game_over = True
                    break
                elif shaft.colliderect(player.rect):
                    score += 1
                    arrows.remove(arrow)

        screen.fill((20, 20, 30))

        pygame.draw.rect(screen, (50, 200, 50), player.rect)

        for arrow in arrows:
            arrow.draw(screen)

        score_surf = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_surf, (10, 10))

        if game_over:
            over_surf = font.render("GAME OVER", True, (255, 80, 80))
            retry_surf = font.render("Press R to Restart", True, (220, 220, 220))
            screen.blit(
                over_surf,
                (WIDTH // 2 - over_surf.get_width() // 2, HEIGHT // 2 - 40)
            )
            screen.blit(
                retry_surf,
                (WIDTH // 2 - retry_surf.get_width() // 2, HEIGHT // 2 + 10)
            )

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
