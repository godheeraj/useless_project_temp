"""
main.py — Main entry point for 'Mosquito Slapping AI'.
Initializes Pygame window, runs the 60 FPS master game loop,
and guarantees clean shutdown and resource cleanup.
"""

import sys
import os
# pyrefly: ignore [missing-import]
import pygame
import config
from game import MosquitoSlapperGame

def set_window_icon():
    """Sets a procedurally generated window icon of a mosquito."""
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(icon, (220, 40, 40), (16, 16), 12)
    pygame.draw.circle(icon, (30, 30, 30), (16, 16), 8)
    pygame.draw.ellipse(icon, (240, 240, 255, 200), (4, 8, 10, 16))
    pygame.draw.ellipse(icon, (240, 240, 255, 200), (18, 8, 10, 16))
    pygame.display.set_icon(icon)

def main():
    print("=" * 65)
    print("MOSQUITO SLAPPING AI")
    print("=" * 65)

    pygame.init()
    pygame.font.init()

    # Set up display surface
    flags = pygame.DOUBLEBUF
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
    pygame.display.set_caption(config.WINDOW_TITLE)
    set_window_icon()

    clock = pygame.time.Clock()
    game = MosquitoSlapperGame(screen)

    running = True
    print("\n[Game] Master loop started. Target FPS:", config.TARGET_FPS)
    print("[Controls] D: Toggle Debug Mode | M: Toggle Demo Mode | ESC: Back/Exit")
    print("[Input] Webcam hands tracking active. Mouse click/Spacebar acts as manual fallback.\n")

    try:
        while running:
            # Tick at target FPS and get delta time in seconds
            dt = clock.tick(config.TARGET_FPS) / 1000.0
            # Clamp dt to avoid physics spiral if window is dragged/paused
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                game.handle_event(event)

            # Master update and render
            game.update(dt)
            game.render()

            pygame.display.flip()

    except KeyboardInterrupt:
        print("\n[Game] Keyboard interrupt detected. Exiting gracefully...")
    except Exception as e:
        print("\n[Game] Unexpected error in main loop:", e)
        import traceback
        traceback.print_exc()
    finally:
        print("[Game] Cleaning up camera and audio resources...")
        game.cleanup()
        pygame.quit()
        print("[Game] Shutdown complete.")

if __name__ == "__main__":
    main()
