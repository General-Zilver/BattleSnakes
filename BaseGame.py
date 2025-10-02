import os
import random
import sys
from typing import List, Set, Tuple, Callable
os.environ['SDL_VIDEO_CENTERED'] = '1' 
import pygame
from customize_board import load_settings

# ─────── constants ────────────────────────────────────────────────────────
ASSETS = os.path.dirname(os.path.abspath(__file__))
LOGO_IMG = os.path.join(ASSETS, "battlesnakes_logo.png")
GRASS_IMG = os.path.join(ASSETS, "grass.png")

CELL = 40
GAP = 20
RIGHT_W = 300  # widened panel for text
SCORES_FILE = "scores.txt"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (170, 170, 170)
RED = (220, 40, 40)
GREEN_BTN = (0, 170, 0)
PANEL_BG = (230, 230, 230)

Coord = Tuple[int, int]

# ─────── model objects ────────────────────────────────────────────────────
class Snake:
    def __init__(self, xy: Coord, sprite: pygame.Surface,
                 move_fn: Callable[["Snake", int, int, Set[Coord], Set[Coord]], None] | None = None):
        self.xy: Coord = xy
        self.sprite = sprite
        self.move_fn = move_fn or Snake.default_move
        self.alive: bool = True
        self.revealed: bool = False  # for bot snakes: revealed when hit

    def hit(self, xy: Coord) -> bool:
        if xy == self.xy:
            self.alive = False
            self.revealed = True
            return True
        return False

    def default_move(self, rows: int, cols: int,
                     blocked: Set[Coord], attacked: Set[Coord]):
        if not self.alive:
            return
        x, y = self.xy
        nbrs = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        random.shuffle(nbrs)
        for nx, ny in nbrs:
            if (0 <= nx < cols and 0 <= ny < rows
                    and (nx, ny) not in blocked
                    and (nx, ny) not in attacked):
                self.xy = (nx, ny)
                return

    def attempt_move(self, rows: int, cols: int,
                     blocked: Set[Coord], attacked: Set[Coord]):
        self.move_fn(self, rows, cols, blocked, attacked)


class Player:
    def __init__(self, name: str):
        self.name = name
        self.snakes: List[Snake] = []
        self.hits: Set[Coord] = set()
        self.misses: Set[Coord] = set()

    def alive_snakes(self):
        return [s for s in self.snakes if s.alive]

    def cells(self) -> Set[Coord]:
        return {s.xy for s in self.snakes if s.alive}

    def all_shots(self) -> Set[Coord]:
        return self.hits | self.misses

    def is_defeated(self) -> bool:
        return not self.alive_snakes()


class BaseGame:
    def __init__(self, settings: dict, user: str = "Player 1"):
        self.rows, self.cols = settings["rows"], settings["cols"]
        self.snakes_each = settings.get("snakes_per_player", 7)
        self.players = [Player(user), Player("Bot")]
        self.turn_idx = 0
        self.turns_taken = 0
        self.phase = "placement"
        self.over = False
        self.last_hit_message = None
        self.hit_timer = 0
        self.force_redraw = False
        self.bot_last_guess = None
        pygame.init()
        self.font = pygame.font.SysFont(None, 22)
#################################################
        original_logo = pygame.image.load(LOGO_IMG)
        self.logo = pygame.transform.smoothscale(original_logo, (600, int(original_logo.get_height() * 600 / original_logo.get_width())))
#################################################
        self.grass = pygame.transform.scale(pygame.image.load(GRASS_IMG), (CELL, CELL))
        self.bot_attack_pending = False
        self.bot_attack_timer = 0
        self.snake_sprites: dict[str, pygame.Surface] = {}
        self._prepare_snake_sprites()
        self.bot_last_hit_message = None

        # Get logo size
        logo_width = self.logo.get_width()
        logo_height = self.logo.get_height()

        board_w = self.cols * CELL
        board_h = self.rows * CELL

        self.left_x = logo_width + GAP

        # Adjust gap between top and bottom board
        gap_between_boards = GAP + 50

        window_w = self.left_x + board_w + GAP + RIGHT_W
        window_h = max(logo_height, board_h * 2 + gap_between_boards)

        self.top_rect = pygame.Rect(self.left_x, 0, board_w, board_h)
        self.bot_rect = self.top_rect.move(0, board_h + gap_between_boards)

        # Setup screen and center the window manually
        self.screen = pygame.display.set_mode((window_w, window_h))
        self.screen.fill(WHITE)
        pygame.display.flip()
        pygame.display.set_caption("BattleSnakes - The Game")

        # Buttons
        self.yes_btn = pygame.Rect(0, 0, 120, 40)
        self.yes_btn.center = (self.left_x + (self.cols * CELL) // 2, self.top_rect.bottom + 30)
        self.play_again_btn = pygame.Rect(self.left_x + board_w + GAP + 50, 300, 120, 40)
        self.quit_btn = pygame.Rect(self.left_x + board_w + GAP + 50, 360, 120, 40)
############
        self.main_menu_btn = pygame.Rect(self.left_x + board_w + GAP + 50, 420, 120, 40)
############

        self.pending: Coord | None = None
        self.messages: List[str] = ["Place your snakes: click bottom grid"]
        self._grass_cache = {}

    def _prepare_snake_sprites(self):
        sprite_names = ["green", "red", "blue", "yellow", "purple", "orange"]
        for cname in sprite_names:
            path = os.path.join(ASSETS, f"{cname}_snake.png")
            if os.path.exists(path):
                img = pygame.image.load(path)
                self.snake_sprites[cname] = pygame.transform.scale(img, (CELL - 6, CELL - 6))
            else:
                print(f"Warning: missing sprite for {cname}")

    def snakes_move_phase(self):
        for p in self.players:
            if p is self.user:
                attacked = self.bot.hits | self.bot.misses # <-- Only bot's hits are dangerous for user snakes
            else:
                attacked = self.user.hits | self.user.misses # <-- Only user's hits are dangerous for bot snakes

            blocked = self.user.cells() | self.bot.cells()
            new_blocked = blocked.copy()

            for s in p.snakes:
                if not s.alive:
                    continue
                new_blocked.discard(s.xy)
                s.attempt_move(self.rows, self.cols, new_blocked, attacked)
                new_blocked.add(s.xy)

            blocked = new_blocked

    def handle_placement_click(self, gx: int, gy: int):
        if len(self.user.snakes) >= self.snakes_each:
            return
        if (gx, gy) in self.user.cells():
            return
        colours = ["green", "red", "blue", "yellow", "purple", "orange"]
        colour = random.choice(colours)
        self.user.snakes.append(Snake((gx, gy), self.snake_sprites[colour]))
        if len(self.user.snakes) == self.snakes_each:
            self.auto_place_bot()
            self.messages.append("Snakes placed – battle begins!")
            self.phase = "battle"

    def auto_place_bot(self):
        colours = ["green", "red", "blue", "yellow", "purple", "orange"]
        while len(self.bot.snakes) < self.snakes_each:
            x, y = random.randrange(self.cols), random.randrange(self.rows)
            if (x, y) not in self.bot.cells() and (x, y) not in self.user.cells():
                c = random.choice(colours)
                self.bot.snakes.append(Snake((x, y), self.snake_sprites[c]))

    def handle_attack_click(self, gx: int, gy: int):
        if (gx, gy) in self.user.all_shots():
            return
        self.pending = (gx, gy)

    def check_game_over(self):
        if self.user.is_defeated():
            self.messages.append("Bot wins! Game over.")
            self.over = True
            self.end_winner = "Bot"
        elif self.bot.is_defeated():
            self.messages.append("You win! Game over.")
            self.over = True
            self.end_winner = "Player"

    def bot_take_shot(self):
        while True:
            x, y = random.randrange(self.cols), random.randrange(self.rows)
            if (x, y) not in self.bot.all_shots():
                break
        self.bot_last_guess = (x, y)
        hit = any(s.hit((x, y)) for s in self.user.snakes)
        (self.bot.hits if hit else self.bot.misses).add((x, y))
        self.messages.append(f"Bot fired at {(x, y)} – {'HIT' if hit else 'miss'}")

        # ✨ NEW: Store bot's popup message
        self.bot_last_hit_message = "Bot: HIT!" if hit else "Bot: MISS!"

        # ✨ NEW: Start popup timer
        self.hit_timer = pygame.time.get_ticks()

    def confirm_attack(self):
        if not self.pending:
            return
        gx, gy = self.pending
        hit = any(s.hit((gx, gy)) for s in self.bot.snakes)

        # --- 1. Update shots
        (self.user.hits if hit else self.user.misses).add((gx, gy))

        # --- 2. Set popup message and timer
        self.last_hit_message = "HIT!" if hit else "MISS!"
        self.hit_timer = pygame.time.get_ticks()

        # --- 3. Update sidebar messages
        self.messages.append(f"You attacked {(gx, gy)} - {self.last_hit_message}")

        self.pending = None
        self.check_game_over()

        if not self.over:
            # Don't attack immediately — set a pending timer instead
            self.bot_attack_pending = True
            self.bot_attack_timer = pygame.time.get_ticks()

    @property
    def user(self) -> Player:
        return self.players[0]

    @property
    def bot(self) -> Player:
        return self.players[1]

    def draw_grid(self, rect: pygame.Rect):
        pygame.draw.rect(self.screen, WHITE, rect)
        for y in range(self.rows):
            for x in range(self.cols):
                abs_x = rect.x + x * CELL
                abs_y = rect.y + y * CELL
                cell = (x, y)

                if rect == self.top_rect:
                    # Top grid: player attacks bot
                    if cell in self.user.misses:
                        pygame.draw.rect(self.screen, WHITE, (abs_x, abs_y, CELL, CELL))
                    else:
                        self.screen.blit(self.grass, (abs_x, abs_y))
                else:
                    # Bottom grid: bot attacks player
                    if cell in self.bot.hits or cell in self.bot.misses:
                        pygame.draw.rect(self.screen, WHITE, (abs_x, abs_y, CELL, CELL))
                    else:
                        self.screen.blit(self.grass, (abs_x, abs_y))

        for x in range(self.cols + 1):
            pygame.draw.line(self.screen, BLACK,
                            (rect.x + x * CELL, rect.y),
                            (rect.x + x * CELL, rect.bottom))
        for y in range(self.rows + 1):
            pygame.draw.line(self.screen, BLACK,
                            (rect.x, rect.y + y * CELL),
                            (rect.right, rect.y + y * CELL))


    def draw_snakes(self, rect: pygame.Rect, owner: Player):
        for s in owner.snakes:
            if not s.alive and not s.revealed:
                continue
            x, y = s.xy

            if owner is self.bot and rect == self.top_rect and not s.revealed:
                continue  # Hide bot snakes unless revealed

            # Draw the snake
            self.screen.blit(s.sprite,
                            (rect.x + x * CELL + 3,
                            rect.y + y * CELL + 3))

            # Draw X if dead
            if not s.alive:
                pygame.draw.line(self.screen, RED,
                                (rect.x + x * CELL + 5, rect.y + y * CELL + 5),
                                (rect.x + (x + 1) * CELL - 5, rect.y + (y + 1) * CELL - 5), 3)
                pygame.draw.line(self.screen, RED,
                                (rect.x + (x + 1) * CELL - 5, rect.y + y * CELL + 5),
                                (rect.x + x * CELL + 5, rect.y + (y + 1) * CELL - 5), 3)


    def draw_attacks(self, rect: pygame.Rect, shooter: Player):
        for x, y in shooter.hits:
            pygame.draw.circle(self.screen, RED,
                               (rect.x + x * CELL + CELL // 2,
                                rect.y + y * CELL + CELL // 2), 8)
        for x, y in shooter.misses:
            pygame.draw.circle(self.screen, GRAY,
                               (rect.x + x * CELL + CELL // 2,
                                rect.y + y * CELL + CELL // 2), 5)

    def draw_panel(self):
        # Right-side panel background
        panel_x = self.left_x + self.cols * CELL + GAP
        panel_rect = pygame.Rect(panel_x, 0, RIGHT_W, self.bot_rect.bottom)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)

        # Render last few messages
        y_offset = 20
        for line in self.messages[-8:]:
            msg_surface = self.font.render(line, True, BLACK)
            self.screen.blit(msg_surface, (panel_x + 10, y_offset))
            y_offset += 24

        # Center button area or placement message
        if self.phase == "placement":
            self.show_snakes_left_message()
        elif self.pending and self.phase == "battle" and self.turn_idx == 0:
            pygame.draw.rect(self.screen, GREEN_BTN, self.yes_btn)
            label = self.font.render("Attack Here?", True, WHITE)
            self.screen.blit(label, label.get_rect(center=self.yes_btn.center))
        ################
        # Always show Quit button
        pygame.draw.rect(self.screen, RED, self.quit_btn)
        quit_text = self.font.render("Quit", True, WHITE)
        self.screen.blit(quit_text, quit_text.get_rect(center=self.quit_btn.center))

        # Always show Main Menu button
        pygame.draw.rect(self.screen, GRAY, self.main_menu_btn)
        main_menu_text = self.font.render("Main Menu", True, WHITE)
        self.screen.blit(main_menu_text, main_menu_text.get_rect(center=self.main_menu_btn.center))
        #####################

    def show_snakes_left_message(self):
        """Show how many snakes left to place during placement phase."""
        snakes_left = self.snakes_each - len(self.user.snakes)
        big_font = pygame.font.SysFont(None, 48)
        message = f"Snakes Left: {snakes_left}"
        color = (0, 180, 0) if snakes_left > 0 else (180, 0, 0)
        surf = big_font.render(message, True, color)
        rect = surf.get_rect(center=(self.left_x + (self.cols * CELL) // 2, self.top_rect.bottom + 30))
        self.screen.blit(surf, rect)


    def draw(self):
        self.screen.fill(WHITE)
        self.screen.fill(WHITE, (0, 0, self.left_x, self.screen.get_height()))
        self.screen.blit(self.logo, (0, 0))
        self.draw_grid(self.top_rect)
        self.draw_grid(self.bot_rect)

        if self.phase == "placement":
            self.draw_snakes(self.bot_rect, self.user)
        else:
            self.draw_snakes(self.bot_rect, self.user)
            self.draw_snakes(self.top_rect, self.bot)
            self.draw_attacks(self.top_rect, self.user)
            self.draw_attacks(self.bot_rect, self.bot)
            if self.pending:
                x, y = self.pending
                pygame.draw.rect(self.screen, (255, 215, 0),
                                (self.top_rect.x + x * CELL + 2,
                                self.top_rect.y + y * CELL + 2,
                                CELL - 4, CELL - 4), 3)

        self.draw_panel()

        if self.over:
            self.draw_end_buttons()

        now = pygame.time.get_ticks()
        if self.last_hit_message and now - self.hit_timer < 1000:
            self.show_popup_message(self.last_hit_message)
        elif self.bot_last_hit_message and now - self.hit_timer < 1000:
            self.show_popup_message(self.bot_last_hit_message)
        else:
            self.last_hit_message = None
            self.bot_last_hit_message = None
        pygame.display.flip()

    def check_game_over(self):
        if self.user.is_defeated():
            self.messages.append("Bot wins! Game over.")
            self.over = True
            self.end_winner = "Bot"
        elif self.bot.is_defeated():
            self.messages.append("You win! Game over.")
            self.over = True
            self.end_winner = "Player"

    def show_popup_message(self, text):
        big_font = pygame.font.SysFont(None, 48)
        if "HIT" in text:
            color = (0, 180, 0)
        else:
            color = (180, 0, 0)
        surf = big_font.render(text, True, color)
        rect = surf.get_rect(center=(self.left_x + (self.cols * CELL) // 2, self.top_rect.bottom + 30))
        self.screen.blit(surf, rect)

    def draw_end_buttons(self):
        # Play Again and Quit buttons
        pygame.draw.rect(self.screen, GREEN_BTN, self.play_again_btn)
        pygame.draw.rect(self.screen, RED, self.quit_btn)
############
        pygame.draw.rect(self.screen, GRAY, self.main_menu_btn)
##############
        again_text = self.font.render("Play Again", True, WHITE)
        quit_text = self.font.render("Quit", True, WHITE)
###########
        menu_text = self.font.render("Main Menu", True, WHITE)
###########
        self.screen.blit(again_text, again_text.get_rect(center=self.play_again_btn.center))
        self.screen.blit(quit_text, quit_text.get_rect(center=self.quit_btn.center))
###########
        self.screen.blit(menu_text, menu_text.get_rect(center=self.main_menu_btn.center))
###########
        # Centered Win/Lose Message (where "Attack Here?" normally is)
        if hasattr(self, "end_winner"):
            big_font = pygame.font.SysFont(None, 48)
            if self.end_winner == "Player":
                result_text = big_font.render("You Win!", True, (0, 180, 0))
            else:
                result_text = big_font.render("Bot Wins!", True, (200, 0, 0))

            # Use the same center as yes_btn
            self.screen.blit(result_text, result_text.get_rect(center=self.yes_btn.center))

    def reset_game(self):
        settings = load_settings()
        self.__init__(settings, self.user.name)

    def play(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            self.draw()

###############################
            if self.over and not hasattr(self, "score_saved"):
                from score_manager import update_score
                update_score(self.user.name, len(self.user.hits))
                self.score_saved = True
###############################

            if self.force_redraw:
                self.force_redraw = False  # reset flag

            # Handle delayed bot attack
            if self.bot_attack_pending and pygame.time.get_ticks() - self.bot_attack_timer >= 1000:
                self.bot_take_shot()
                self.check_game_over()
                if not self.over:
                    self.snakes_move_phase()
                    self.turns_taken += 1
                self.bot_attack_pending = False

            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self.quit_btn.collidepoint(e.pos):
                        running = False
                    elif self.over and self.play_again_btn.collidepoint(e.pos):
                        self.reset_game()
#################################
                    elif self.main_menu_btn.collidepoint(e.pos):
                        pygame.mixer.quit()  # if using sound, clean up
                        self.over = True     # optional: flag to exit cleanly
                        from main import run_gui_launcher
                        run_gui_launcher()
                        return
#############################
                    elif self.phase == "placement" and self.bot_rect.collidepoint(e.pos):
                        gx = (e.pos[0] - self.bot_rect.x) // CELL
                        gy = (e.pos[1] - self.bot_rect.y) // CELL
                        self.handle_placement_click(gx, gy)

                    elif self.phase == "battle":
                        if self.yes_btn.collidepoint(e.pos) and self.pending:
                            self.confirm_attack()
                        elif self.top_rect.collidepoint(e.pos):
                            gx = (e.pos[0] - self.top_rect.x) // CELL
                            gy = (e.pos[1] - self.top_rect.y) // CELL
                            self.handle_attack_click(gx, gy)

            clock.tick(30)

        pygame.quit()
        sys.exit()
