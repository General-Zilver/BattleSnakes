import pygame
from customize_board import customize_board_gui, load_settings, reset_to_defaults
from Difficulty import EasyGame, RegularGame, HardGame
import sys
import os

SCORES_FILE = "scores.txt"

# Colors and fonts
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

pygame.init()
FONT = pygame.font.SysFont(None, 32)
BIG_FONT = pygame.font.SysFont(None, 48)

def draw_button(screen, rect, label, mouse_pos):
    color = DARK_GRAY if rect.collidepoint(mouse_pos) else GRAY
    pygame.draw.rect(screen, color, rect)
    text = FONT.render(label, True, WHITE)
    screen.blit(text, text.get_rect(center=rect.center))

def show_scores_gui(screen):
    screen.fill(BLACK)

    scores = []
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE) as f:
            for line in f:
                parts = line.strip().rsplit(" ", 1)  # Split on last space
                if len(parts) == 2 and parts[1].isdigit():
                    username, score = parts
                    scores.append((username, int(score)))
    if not scores:
        lines = ["No scores yet."]
    else:
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        lines = scores[:10]

    # Title
    screen.blit(BIG_FONT.render("------Scores------", True, WHITE), (50, 10))
    screen.blit(FONT.render("Players", True, WHITE), (50, 50))
    screen.blit(FONT.render("-----------", True, WHITE), (50, 60))
    screen.blit(FONT.render("Score", True, WHITE), (300, 50))
    screen.blit(FONT.render("---------", True, WHITE), (300, 60))

    #Controls the starting vertical position of each line of text
    y = 90
    for name, score in lines:
        name_txt = FONT.render(name, True, WHITE)
        score_txt = FONT.render(str(score), True, WHITE)
        screen.blit(name_txt, (50, y))    # Left column
        screen.blit(score_txt, (300, y))  # Right column
        y += 30

    pygame.display.flip()
    pygame.time.wait(5000)#keeps the score screen visiblee for 5 seconds

def run_gui_launcher():
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("BattleSnakes - Menu")

    clock = pygame.time.Clock()
    input_active = True
    username = ""
    input_box = pygame.Rect(180, 60, 240, 40)

    # Buttons
    buttons = {
        "easy": pygame.Rect(200, 130, 200, 40),
        "regular": pygame.Rect(200, 180, 200, 40),
        "hard": pygame.Rect(200, 230, 200, 40),
        "custom": pygame.Rect(200, 280, 200, 40),
        "scores": pygame.Rect(200, 330, 95, 30),
        "quit": pygame.Rect(305, 330, 95, 30),
    }

    while True:
        screen.fill(BLACK)
        mouse_pos = pygame.mouse.get_pos()

        # Title
        title = BIG_FONT.render("BattleSnakes", True, RED)
        screen.blit(title, title.get_rect(center=(300, 30)))

        # Username input
        pygame.draw.rect(screen, BLACK, input_box, 2)
        name_txt = FONT.render(username or "Enter username...", True, WHITE)
        screen.blit(name_txt, (input_box.x + 10, input_box.y + 8))

        # Buttons
        draw_button(screen, buttons["easy"], "Play Easy", mouse_pos)
        draw_button(screen, buttons["regular"], "Play Regular", mouse_pos)
        draw_button(screen, buttons["hard"], "Play Hard", mouse_pos)
        draw_button(screen, buttons["custom"], "Customize Board", mouse_pos)
        draw_button(screen, buttons["scores"], "Scores", mouse_pos)
        draw_button(screen, buttons["quit"], "Quit", mouse_pos)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.KEYDOWN and input_active:
                if e.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif e.key == pygame.K_RETURN:
                    input_active = False
                else:
                    username += e.unicode
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if buttons["easy"].collidepoint(mouse_pos):
                    EasyGame(load_settings(), username or "Guest").play()
                elif buttons["regular"].collidepoint(mouse_pos):
                    RegularGame(load_settings(), username or "Guest").play()
                elif buttons["hard"].collidepoint(mouse_pos):
                    HardGame(load_settings(), username or "Guest").play()
                elif buttons["custom"].collidepoint(mouse_pos):
                    customize_board_gui()
                elif buttons["scores"].collidepoint(mouse_pos):
                    show_scores_gui(screen)
                elif buttons["quit"].collidepoint(mouse_pos):
                    pygame.quit(); sys.exit()

        clock.tick(30)

if __name__ == "__main__":
    reset_to_defaults()
    run_gui_launcher()