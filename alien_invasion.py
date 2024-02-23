import sys
from time import sleep
import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    """"Overall class to manage game assets and behavior."""

    def __init__(self) -> None:
        """Initialize the game, and create game resources"""
        pygame.init ()

        self.clock = pygame.time.Clock ()
        self.screen = pygame.display.set_mode ((0,0), pygame.FULLSCREEN)
        self.settings = Settings ()
        self.settings.screen_width = self.screen.get_rect ().width
        self.settings.screen_height = self.screen.get_rect ().height
        self.bg_color = self.settings.bg_color
        pygame.display.set_caption ("Alien Invasion")

        self.stats = GameStats (self)
        self.scoreboard = Scoreboard (self)

        self.ship = Ship (self)
        self.bullets = pygame.sprite.Group ()
        self.aliens = pygame.sprite.Group ()

        # Make the Play button.
        self.play_button = Button (self, "Play")

        # Start Alien Invasion in an active state
        self.game_active = False


    def _create_alien (self, x_position, y_position):
        """Create one alien and place it in the row."""
        new_alien = Alien (self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add (new_alien)

    def _create_alien_fleet (self):
        """Create the fleet of aliens."""
        # Create an alien and keep adding aliens until there is no room
        # Spacing between aliens is on alien width
        alien = Alien (self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 3 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien (current_x, current_y)
                current_x += 2 * alien_width
            # Finished a row; reset x value, increment y value
            current_x = alien_width
            current_y += 2 * alien_height

    def _restart_game (self):
            # Get rid of any remaining bullets and aliens.
            self.bullets.empty ()
            self.aliens.empty ()

            # Create a new fleet and center the ship
            self._create_alien_fleet ()
            self.ship.center_ship ()

    def _ship_hit (self):
        """Respond to the ship being hit by an alien"""
        if self.stats.ships_left > 0:
            # Decrement ships_left.
            self.stats.ships_left -= 1
            self.scoreboard.prep_ships ()

            self._restart_game ()
            sleep (0.5)
        else:
            self.game_active = False

    def _fire_bullet (self):
        """Create a new bullet and add it to the bullets group."""
        if len (self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet (self)
            self.bullets.add (new_bullet)

    def _check_play_button (self, mouse_pos):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint (mouse_pos)
        if button_clicked and not self.game_active:
            # Reset game dynamic settings
            self.settings.initialize_dynamic_settings ()
            # Reset the game statistics.
            self.stats.reset_stats ()
            self.scoreboard.prep_score ()
            self.scoreboard.prep_level ()
            self.scoreboard.prep_ships ()
            self.game_active = True

            self._restart_game ()

    def _check_keydown_event (self, event):
        """Respond to key press event."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_SPACE:
            self._fire_bullet ()
        elif event.key == pygame.K_q:
            sys.exit ()

    def _check_keyup_event (self, event):
        """Respond to key release event."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _check_events (self):
        for event in pygame.event.get ():
            if event.type == pygame.QUIT:
                sys.exit ()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if (not self.game_active):
                    mouse_pos = pygame.mouse.get_pos ()
                    self._check_play_button (mouse_pos)
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_event (event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_event (event)

    def _change_fleet_direction (self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites ():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_fleet_edges (self):
        """Respond appropriately if any alien has reached an edge."""
        for alien in self.aliens.sprites ():
            if alien.is_at_screen_edge ():
                self._change_fleet_direction ()
                break
    
    def _check_bullet_alien_collisions (self):
        """Respond to bullet-alien collisions."""
        # Check for any bullets that have hit aliens.
        # If so, then get rid of the bullet and the alien.
        collisions = pygame.sprite.groupcollide (self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values ():
                self.stats.score += self.settings.alien_points * len (aliens)
            self.scoreboard.prep_score ()
            self.scoreboard.check_high_score ()

        if not self.aliens:
            # Destroy existing bullets and create new fleet.
            self.bullets.empty ()
            self._create_alien_fleet ()
            self.settings.increase_speed ()

            # Increase level.
            self.stats.level += 1
            self.scoreboard.prep_level ()

    def _update_bullets (self):
        """Update position of bullets and get rid of old bullets"""
        self.bullets.update ()

        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy ():
            if bullet.rect.bottom < 50:
                self.bullets.remove (bullet)

        self._check_bullet_alien_collisions ()

    def _update_screen (self):
        """Update images on the screen,and flip to the new screen."""
        self.screen.fill (self.settings.bg_color)

        for bullet in self.bullets.sprites ():
            bullet.draw_bullet ()

        self.ship.blitme ()

        self.aliens.draw (self.screen)

        self.scoreboard.show_score ()

        if not self.game_active:
            self.play_button.draw_button ()

        # Make the most recently drawn screen visible.
        pygame.display.flip ()

    def _check_aliens_bottom (self):
        """Check if any aliens have reached the bottom of the screen."""
        for alien in self.aliens.sprites ():
            if alien.rect.bottom >= self.settings.screen_height:
                # Treat this the same as if the ship got hit.
                self._ship_hit ()
                break

    def _update_aliens (self):
        """Update the positions of all aliens in the fleet"""
        if (not self.aliens):
            self.bullets.empty ()
            self._create_alien_fleet ()

        self._check_fleet_edges ()
        self.aliens.update ()

        # Look for alien-ship collisions
        if pygame.sprite.spritecollideany (self.ship, self.aliens):
            self._ship_hit ()

        # Look for aliens hitting the bottom of the screen.
        self._check_aliens_bottom ()

    def run_game (self):
        """Start the main loop for the game."""
        while True:
            # Watch for keyboard and mouse events.
            self._check_events ()

            if self.game_active:
                self.ship.update ()
                self._update_bullets ()
                self._update_aliens ()

            self._update_screen ()
            self.clock.tick (self.settings.ticks)

if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion ()
    ai.run_game ()