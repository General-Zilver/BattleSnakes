# customize_board.py – configure board size & snake count
import json
import os
import pygame
import sys

SETTINGS_FILE = "board_settings.json"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (170, 170, 170)
RED = (220, 40, 40)
GREEN_BTN = (0, 170, 0)
PANEL_BG = (230, 230, 230)

DEFAULTS = {
    "rows": 10,
    "cols": 10,
    "snakes_per_player": 7
}
def reset_to_defaults() -> None:
    """Force the settings file to match DEFAULTS every time the game starts."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(DEFAULTS, f)
pygame.init()
FONT = pygame.font.SysFont(None, 32)
BIG_FONT = pygame.font.SysFont(None, 48)
def draw_button(screen, rect, label, mouse_pos):
    color = GRAY if rect.collidepoint(mouse_pos) else GRAY
    pygame.draw.rect(screen, color, rect)
    text = FONT.render(label, True, WHITE)
    screen.blit(text, text.get_rect(center=rect.center))

def _prompt_int(label: str, default: int) -> int:
    val = input(f"{label} (default {default}): ").strip()
    try:
        return int(val) if val else default
    except ValueError:
        print("Invalid – keeping default.")
        return default


def customize_board() -> None:
    print("\n--- Customize Board ---")
    settings = DEFAULTS.copy()
    settings["rows"] = _prompt_int("Board rows", settings["rows"])
    settings["cols"] = _prompt_int("Board columns", settings["cols"])
    settings["snakes_per_player"] = _prompt_int(
        "Snakes per player", settings["snakes_per_player"]
    )

    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)
    print("✔  Settings saved.")


def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            return {**DEFAULTS, **data}
        except (json.JSONDecodeError, IOError):
            print("⚠ Failed to load settings. Using defaults.")
    return DEFAULTS.copy()
def customize_board_gui():
    screen = pygame.display.set_mode((700, 500))  # Larger window
    pygame.display.set_caption("Customize BattleSnakes Board")

    clock = pygame.time.Clock()

    settings = DEFAULTS.copy()

    fields = {
        "rows": pygame.Rect(250, 100, 200, 40),
        "cols": pygame.Rect(250, 170, 200, 40),
        "snakes_per_player": pygame.Rect(250, 240, 200, 40),
    }

    input_texts = {
        "rows": str(settings["rows"]),
        "cols": str(settings["cols"]),
        "snakes_per_player": str(settings["snakes_per_player"]),
    }

    active_field = None
    blink = True
    blink_timer = 0

    # Buttons
    save_button = pygame.Rect(180, 350, 120, 40)
    cancel_button = pygame.Rect(400, 350, 120, 40)

    running = True
    while running:
        screen.fill(BLACK)
        mouse_pos = pygame.mouse.get_pos()

        # Title
        title = BIG_FONT.render("Customize Board", True, RED)
        screen.blit(title, title.get_rect(center=(350, 40)))

        # Draw input fields
        for field, rect in fields.items():
            color = RED if active_field == field else WHITE
            pygame.draw.rect(screen, color, rect, 2)

            display_text = input_texts[field]
            # Add blinking cursor if active
            if active_field == field and blink:
                display_text += "|"

            text_surface = FONT.render(display_text, True, WHITE)
            screen.blit(text_surface, (rect.x + 10, rect.y + 8))

            label = FONT.render(field.replace("_", " ").capitalize(), True, WHITE)
            screen.blit(label, (rect.x - 200, rect.y + 8))

        # Draw buttons
        draw_button(screen, save_button, "Save", mouse_pos)
        draw_button(screen, cancel_button, "Cancel", mouse_pos)

        pygame.display.flip()

        # Blinking cursor timer
        blink_timer += clock.get_time()
        if blink_timer >= 500:  # Toggle blink every 500ms
            blink = not blink
            blink_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if save_button.collidepoint(mouse_pos):
                    # Save settings
                    try:
                        # Parse input values
                        for key in fields:
                            settings[key] = int(input_texts[key])
                        
                        rows = settings["rows"]
                        cols = settings["cols"]
                        snakes = settings["snakes_per_player"]
                        total_cells = rows * cols
                        required_cells = snakes * 2

                        if required_cells > total_cells:
                            print(f"⚠ Too many snakes! Board has {total_cells} cells, but needs {required_cells}.")
                            continue  # Skip saving and stay in GUI

                        # Save to file
                        with open(SETTINGS_FILE, "w") as f:
                            json.dump(settings, f)
                        print("✔ Settings saved!")
                        running = False

                    except ValueError:
                        print("⚠ Invalid input! Settings not saved.")
                    running = False
                elif cancel_button.collidepoint(mouse_pos):
                    running = False
                else:
                    # Check which field is clicked
                    active_field = None
                    for field, rect in fields.items():
                        if rect.collidepoint(mouse_pos):
                            active_field = field

            elif event.type == pygame.KEYDOWN and active_field:
                if event.key == pygame.K_BACKSPACE:
                    input_texts[active_field] = input_texts[active_field][:-1]
                elif event.key == pygame.K_RETURN:
                    active_field = None
                elif event.unicode.isdigit():
                    input_texts[active_field] += event.unicode

        clock.tick(30)
