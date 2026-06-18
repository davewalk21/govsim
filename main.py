import pygame

from views.chamber import ChamberView
from views.dropdown import Dropdown
from views.map_view import MapView

SCREEN_SIZE = (1280, 800)
FPS = 60

VIEW_OPTIONS = [
    ("Senate", "senate"),
    ("House", "house"),
    ("Map", "map"),
]


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("GovSim")
    clock = pygame.time.Clock()

    views = {
        "senate": ChamberView("U.S. Senate (100 seats)", 100, 4, SCREEN_SIZE),
        "house": ChamberView("U.S. House (435 seats)", 435, 11, SCREEN_SIZE),
        "map": MapView(SCREEN_SIZE),
    }
    active_view = "senate"
    dropdown = Dropdown(
        pygame.Rect(24, 16, 220, 36),
        VIEW_OPTIONS,
        active_view,
    )

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif dropdown.handle_event(event):
                active_view = dropdown.selected_key
            elif not dropdown.open:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        active_view = "senate"
                        dropdown.set_selected("senate")
                    elif event.key == pygame.K_2:
                        active_view = "house"
                        dropdown.set_selected("house")
                    elif event.key == pygame.K_3:
                        active_view = "map"
                        dropdown.set_selected("map")
                    else:
                        views[active_view].handle_event(event)
                else:
                    views[active_view].handle_event(event)

        views[active_view].draw(screen)
        dropdown.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
