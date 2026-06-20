import pygame

from core.government import Government
from views.chamber import ChamberView
from views.dropdown import Dropdown
from views.map_view import GovernorMapView, HouseMapView, SenateMapView

SCREEN_SIZE = (1280, 800)
FPS = 60

VIEW_OPTIONS = [
    ("Senate", "senate_chamber"),
    ("Senate Map", "senate_map"),
    ("House", "house_chamber"),
    ("House Map", "house_map"),
    ("Governors", "governor_chamber"),
    ("Governors Map", "governor_map"),
]

VIEW_KEYS = {
    pygame.K_1: "senate_chamber",
    pygame.K_2: "senate_map",
    pygame.K_3: "house_chamber",
    pygame.K_4: "house_map",
    pygame.K_5: "governor_chamber",
    pygame.K_6: "governor_map",
}


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("GovSim")
    clock = pygame.time.Clock()

    government = Government.create_default()
    views = {
        "senate_chamber": ChamberView(
            "U.S. Senate (100 seats)", government.senate, 4, SCREEN_SIZE
        ),
        "senate_map": SenateMapView(SCREEN_SIZE, government.senate),
        "house_chamber": ChamberView(
            "U.S. House (435 seats)", government.house, 11, SCREEN_SIZE
        ),
        "house_map": HouseMapView(SCREEN_SIZE, government.house),
        "governor_chamber": ChamberView(
            "U.S. Governors (50 seats)", government.governors, 4, SCREEN_SIZE
        ),
        "governor_map": GovernorMapView(SCREEN_SIZE, government.governors),
    }
    active_view = "senate_chamber"
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
                if event.type == pygame.KEYDOWN and event.key in VIEW_KEYS:
                    active_view = VIEW_KEYS[event.key]
                    dropdown.set_selected(active_view)
                else:
                    views[active_view].handle_event(event)

        views[active_view].draw(screen)
        dropdown.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
