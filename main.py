from __future__ import annotations

from enum import Enum

import pygame

from core.election import PresidentialElection
from core.government import Government
from core.party import Party
from views.campaign_setup import CampaignSetupScreen
from views.chamber import BenchChamberView, ChamberView
from views.election_map import ElectionCampaignView
from views.game_bar import ElectionGameBar
from views.home import HomeScreen
from views.map_view import GovernorMapView, HouseMapView, SenateMapView
from views.nav import ViewNavigator
from views.party_roster import RosterView

SCREEN_SIZE = (1280, 800)
FPS = 60


class AppMode(Enum):
    HOME = "home"
    CAMPAIGN_SETUP = "campaign_setup"
    DEV = "dev"
    ELECTION = "election"


class App:
    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.mode = AppMode.HOME
        self.home = HomeScreen(screen_size)
        self.campaign_setup = CampaignSetupScreen(screen_size)
        self.government: Government | None = None
        self.navigator: ViewNavigator | None = None
        self.views: dict | None = None
        self.election: PresidentialElection | None = None
        self.election_view: ElectionCampaignView | None = None
        self.game_bar: ElectionGameBar | None = None

    def start_dev_mode(self) -> None:
        self.government = Government.create_default()
        self.views = {
            "senate_chamber": ChamberView(
                "U.S. Senate (100 seats)", self.government.senate, 4, self.screen_size
            ),
            "senate_map": SenateMapView(self.screen_size, self.government.senate),
            "senate_roster": RosterView(self.screen_size, self.government.senate, "Senate"),
            "house_chamber": ChamberView(
                "U.S. House (435 seats)", self.government.house, 11, self.screen_size
            ),
            "house_map": HouseMapView(self.screen_size, self.government.house),
            "house_roster": RosterView(self.screen_size, self.government.house, "House"),
            "governors_chamber": ChamberView(
                "U.S. Governors (50 seats)", self.government.governors, 4, self.screen_size
            ),
            "governors_map": GovernorMapView(self.screen_size, self.government.governors),
            "governors_roster": RosterView(
                self.screen_size, self.government.governors, "Governors"
            ),
            "court_chamber": BenchChamberView(
                "U.S. Supreme Court (9 seats)", self.government.court, self.screen_size
            ),
            "court_roster": RosterView(self.screen_size, self.government.court, "Court"),
        }
        self.navigator = ViewNavigator()
        self.navigator.set_screen_width(self.screen_size[0])
        self.mode = AppMode.DEV

    def go_home(self) -> None:
        self.mode = AppMode.HOME
        self.government = None
        self.navigator = None
        self.views = None
        self.election = None
        self.election_view = None
        self.game_bar = None

    def start_new_game(
        self,
        player_party: Party,
        dem_platform: dict[str, float],
        rep_platform: dict[str, float],
    ) -> None:
        player_promises = dem_platform if player_party == Party.DEMOCRAT else rep_platform
        opponent_promises = rep_platform if player_party == Party.DEMOCRAT else dem_platform
        self.election = PresidentialElection.create_new(
            player_party=player_party,
            player_promises=player_promises,
            opponent_promises=opponent_promises,
        )
        self.election_view = ElectionCampaignView(self.screen_size, self.election)
        self.game_bar = ElectionGameBar(self.screen_size)
        self._sync_election_bar()
        self.mode = AppMode.ELECTION

    def _sync_election_bar(self) -> None:
        if self.game_bar is None or self.election is None:
            return
        self.game_bar.set_countdown(
            self.election.countdown_label(),
            button_enabled=self.election.button_enabled(),
            button_label=self.election.button_label(),
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return False to quit the application."""
        if event.type == pygame.QUIT:
            return False

        if self.mode == AppMode.HOME:
            self.home.handle_event(event)
            action = self.home.pending_action
            if action == "new_game":
                self.home.pending_action = None
                self.campaign_setup.reset()
                self.mode = AppMode.CAMPAIGN_SETUP
            elif action == "dev_mode":
                self.home.pending_action = None
                self.start_dev_mode()
            elif action == "exit":
                return False
            return True

        if self.mode == AppMode.CAMPAIGN_SETUP:
            self.campaign_setup.handle_event(event)
            if self.campaign_setup.consume_back():
                self.mode = AppMode.HOME
                return True
            start_config = self.campaign_setup.consume_start()
            if start_config:
                player_party, dem_platform, rep_platform = start_config
                self.start_new_game(player_party, dem_platform, rep_platform)
                self.mode = AppMode.ELECTION
            return True

        if self.mode == AppMode.ELECTION:
            if self.game_bar and self.game_bar.handle_event(event):
                if self.game_bar.consume_home():
                    self.go_home()
                    return True
                if self.game_bar.consume_next_turn() and self.election:
                    if self.election.on_election_day:
                        self.election.start_reveal()
                        if self.election_view:
                            self.election_view.reset_state_filter()
                    else:
                        self.election.next_turn()
                    self._sync_election_bar()
                return True
            if self.election_view and self.election_view.handle_event(event):
                return True
            return True

        if self.mode == AppMode.DEV:
            assert self.navigator is not None and self.views is not None
            active_key = self.navigator.active_view_key
            active_view = self.views[active_key]
            if active_key.endswith("_roster"):
                active_view.set_party(self.navigator.party)

            if self.navigator.handle_event(event):
                if self.navigator.consume_home():
                    self.go_home()
                    return True
                return True
            active_view.handle_event(event)
            return True

        return True

    def update(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        if self.mode == AppMode.DEV and self.navigator and self.views:
            active_view = self.views[self.navigator.active_view_key]
            if hasattr(active_view, "update_hover"):
                active_view.update_hover(mouse_pos)
        if self.mode == AppMode.ELECTION and self.election_view:
            if hasattr(self.election_view, "update_hover"):
                self.election_view.update_hover(mouse_pos)
        if self.mode == AppMode.ELECTION and self.election and self.election.revealing:
            if self.election.tick_reveal(pygame.time.get_ticks()):
                self._sync_election_bar()

    def draw(self, surface: pygame.Surface) -> None:
        if self.mode == AppMode.HOME:
            self.home.draw(surface)
        elif self.mode == AppMode.CAMPAIGN_SETUP:
            self.campaign_setup.draw(surface)
        elif self.mode == AppMode.ELECTION:
            assert self.election_view is not None and self.game_bar is not None
            self.election_view.draw(surface)
            self.game_bar.draw(surface)
        elif self.mode == AppMode.DEV:
            assert self.navigator is not None and self.views is not None
            self.views[self.navigator.active_view_key].draw(surface)
            self.navigator.draw(surface)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("GovSim")
    clock = pygame.time.Clock()
    app = App(SCREEN_SIZE)

    running = True
    while running:
        for event in pygame.event.get():
            if not app.handle_event(event):
                running = False
                break

        app.update()
        app.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
