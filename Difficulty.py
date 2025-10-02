from BaseGame import BaseGame, CELL, GAP, RIGHT_W, WHITE, BLACK, GRAY, RED, GREEN_BTN, PANEL_BG, Player
import pygame
import os
import random
from typing import List, Set, Tuple, Callable, Optional

Coord = Tuple[int, int]
class RegularGame(BaseGame):
    """Regular mode: standard 1-cell attack behavior."""
    def confirm_attack(self):
        if not self.pending:
            return
        gx, gy = self.pending
        hit = any(s.hit((gx, gy)) for s in self.bot.snakes)
        (self.user.hits if hit else self.user.misses).add((gx, gy))
        self.messages.append(f"You attacked {(gx, gy)} - {'HIT' if hit else 'miss'}")
        self.pending = None
        self.check_game_over()
        if not self.over:
            self.bot_attack_pending = True
            self.bot_attack_timer = pygame.time.get_ticks()

class EasyGame(BaseGame):
    """Easy mode: attacks a cross shape (center + N/S/E/W)"""
    def confirm_attack(self):
        if not self.pending:
            return
        x, y = self.pending
        targets = {(x, y), (x+1, y), (x-1, y), (x, y+1), (x, y-1)}
        hit_any = False
        for gx, gy in targets:
            if 0 <= gx < self.cols and 0 <= gy < self.rows:
                if any(s.hit((gx, gy)) for s in self.bot.snakes):
                    self.user.hits.add((gx, gy))
                    hit_any = True
                else:
                    self.user.misses.add((gx, gy))

        self.last_hit_message = "HIT!" if hit_any else "MISS!"
        self.hit_timer = pygame.time.get_ticks()

        self.messages.append(f"You attacked {self.pending} + neighbors - {self.last_hit_message}")
        self.pending = None
        self.check_game_over()
        if not self.over:
            self.bot_attack_pending = True
            self.bot_attack_timer = pygame.time.get_ticks()


class HardGame(BaseGame):
    """Hard mode: only hits reveal snakes. Grass regrows except last guess."""
    def handle_attack_click(self, gx: int, gy: int):
        self.pending = (gx, gy)
    def __init__(self, settings: dict, user: str = "Player 1"):
        super().__init__(settings, user)
        self.last_guess: Optional[Coord] = None
        self.force_redraw = False
        self.last_hit_message = None
        self.hit_timer = 0
        self.bot_last_guess: Optional[Coord] = None
        
    def draw(self):
        self.screen.fill(WHITE)
        self.screen.blit(self.logo, (0, 0))
        self.draw_grid(self.top_rect)
        self.draw_grid(self.bot_rect)

        if self.phase == "placement":
            self.draw_snakes(self.bot_rect, self.user)
        else:
            self.draw_snakes(self.bot_rect, self.user)
            self.draw_snakes(self.top_rect, self.bot)

            # Only draw player's hits
            self.draw_attacks(self.top_rect, self.user)
            self.draw_attacks(self.bot_rect, self.bot)

            if self.pending:
                x, y = self.pending
                pygame.draw.rect(self.screen, (255, 215, 0),
                                 (self.top_rect.x + x * CELL + 2,
                                  self.top_rect.y + y * CELL + 2,
                                  CELL - 4, CELL - 4), 3)

        self.draw_panel()
        if self.last_hit_message and pygame.time.get_ticks() - self.hit_timer < 1000:
            self.show_popup_message(self.last_hit_message)

        pygame.display.flip()

    def confirm_attack(self):
        if not self.pending:
            return
        gx, gy = self.pending
        hit = any(s.hit((gx, gy)) for s in self.bot.snakes)
        (self.user.hits if hit else self.user.misses).add((gx, gy))
        self.last_guess = (gx, gy)
        self.last_hit_message = "HIT!" if hit else "MISS!"
        self.hit_timer = pygame.time.get_ticks()

        self.messages.append(f"You attacked {(gx, gy)} - {self.last_hit_message}")
        self.pending = None
        self.check_game_over()
        if not self.over:
            self.bot_attack_pending = True
            self.bot_attack_timer = pygame.time.get_ticks()

    def snakes_move_phase(self):
        attacked = self.user.hits | self.bot.hits
        for p in self.players:
            blocked = self.user.cells() | self.bot.cells()
            for s in p.snakes:
                s.attempt_move(self.rows, self.cols, blocked, attacked)
                blocked = self.user.cells() | self.bot.cells()
    def draw_grid(self, rect: pygame.Rect):
        for y in range(self.rows):
            for x in range(self.cols):
                abs_x = rect.x + x * CELL
                abs_y = rect.y + y * CELL
                cell = (x, y)

                if rect == self.top_rect:
                    # Top board (attack bot):
                    if cell in self.user.hits:
                        pygame.draw.rect(self.screen, WHITE, (abs_x, abs_y, CELL, CELL))
                    elif self.last_guess == cell:
                        pygame.draw.rect(self.screen, WHITE, (abs_x, abs_y, CELL, CELL))
                    else:
                        self.screen.blit(self.grass, (abs_x, abs_y))
                else:
                    # Bottom board (bot attacks you):
                    if cell in self.bot.hits:
                        pygame.draw.rect(self.screen, WHITE, (abs_x, abs_y, CELL, CELL))
                    elif self.bot_last_guess == cell:
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

    
    def draw_attacks(self, rect: pygame.Rect, shooter: Player):
        if shooter is self.user:
            for x, y in shooter.hits:
                pygame.draw.circle(self.screen, RED,
                                   (rect.x + x * CELL + CELL // 2,
                                    rect.y + y * CELL + CELL // 2), 8)

