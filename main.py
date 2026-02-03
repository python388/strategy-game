import pygame
import sys
from game_board import GameBoard
from board_renderer import BoardRenderer
import statreader
import ai
from colors import COLORS

# Game Constants
FPS = 60
WINDOW_TITLE = "Strategy Game"
TILE_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

class StrategyGame:
    """Main game class using the new split architecture"""
    
    def __init__(self):
        """Initialize the game with separate logic and rendering"""
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Create game logic (no pygame dependencies)
        self.game_board = GameBoard(
            width=BOARD_WIDTH, 
            height=BOARD_HEIGHT
        )

        # Create renderer (handles all pygame/visual stuff)
        self.renderer = BoardRenderer(self.game_board, TILE_SIZE)
        
        # Game state
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize game scenario
        self.setup_castle_scenario()
        
        print("Strategy Game Initialized!")
    
    def setup_castle_scenario(self):
        """Set up the classic castle vs castle scenario"""
        # Player 0 (Blue team) - Bottom castle
        self._build_castle(player_id=0, castle_y=0, wall_y=3, gate_y=3, archer_y=1)
        
        # Player 1 (Red team) - Top castle  
        self._build_castle(player_id=1, castle_y=19, wall_y=16, gate_y=16, archer_y=18)
        
        print("Castle scenario loaded!")
        print(f"Player 0 (Blue): {self.game_board.get_player_num(0).getMoney()} gold")
        print(f"Player 1 (Red): {self.game_board.get_player_num(1).getMoney()} gold")

        # Register a simple heuristic AI for Player 1 (Red)
        # You can toggle this or register different AI controllers as needed
        self.game_board.get_player_num(1).setIsAI(True)
        self.game_board.register_ai(self.game_board.get_player_num(1), ai.HeuristicAI(self.game_board.get_player_num(1)))
    
    def _build_castle(self, player_id, castle_y, wall_y, gate_y, archer_y):
        """Helper to build one player's castle complex"""
        # Main wall (6 tiles wide)
        for i in range(6):
            self.game_board.initialize_unit(i+2, wall_y, 'statsheets/Wall.txt', player_id, prebuilt=True, tile_dimensions=30)
        
        # Side walls (3 tiles high on each side)
        wall_start_y = 0 if player_id == 0 else 17
        for i in range(3):
            self.game_board.initialize_unit(2, wall_start_y + i, 'statsheets/Wall.txt', player_id, prebuilt=True, tile_dimensions=30)
            self.game_board .initialize_unit(7, wall_start_y + i, 'statsheets/Wall.txt', player_id, prebuilt=True, tile_dimensions=30)
        
        # Gates (2 tiles for entrance)
        self.game_board.initialize_unit(4, gate_y, 'statsheets/Gate.txt', player_id, prebuilt=True, tile_dimensions=30)
        self.game_board.initialize_unit(5, gate_y, 'statsheets/Gate.txt', player_id, prebuilt=True, tile_dimensions=30)
        
        # Defensive archer
        self.game_board.initialize_unit(5, archer_y, 'statsheets/Archer.txt', player_id, tile_dimensions=30)
        
        # Castle (command center) and Farm (economy)
        self.game_board.initialize_unit(5, castle_y, 'statsheets/Castle.txt', player_id, prebuilt=True, tile_dimensions=30)
        self.game_board.initialize_unit(4, castle_y, 'statsheets/Farm.txt', player_id, prebuilt=True, tile_dimensions=30)
    
    def handle_events(self):
        """Process all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.shutdown()
            
            elif event.type == pygame.KEYDOWN:
                self.handle_keypress(event.key)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.pos, event.button)
            
            elif event.type == pygame.VIDEORESIZE:
                self.handle_resize()
    
    def handle_keypress(self, key):
        """Handle keyboard input"""
        if key == pygame.K_SPACE:
            self.advance_turn()
        
        elif key == pygame.K_ESCAPE:
            self.shutdown()
        
        elif key == pygame.K_l:
            self.restart_game()
        
        elif key == pygame.K_h:
            self.show_help()
        
        else:
            try:
                self.renderer.UI.handle_keypress(chr(key))
            except:
                print(str(key) + " (not convertible to character via ascii)")

    def handle_resize(self) -> None:
        self.renderer.resize_window()

    def handle_mouse_click(self, pos, button):
        """Handle mouse clicks"""
        if button == 1:  # Left click
            # Check if click was handled by UI
            ui_handled = self.renderer.handle_click(pos)
            if not ui_handled:
                pass
    
    def advance_turn(self):
        """Advance to the next turn"""
        current_player = self.game_board.get_player_acting()
        self.game_board.next_turn()
        new_player = self.game_board.get_player_acting()
        print(f"Turn advanced! Now Player {new_player.getTeam()}'s turn")
        print(f"Player {new_player.getTeam()} has {new_player.getMoney()} gold")
    
    def restart_game(self):
        """Restart the game"""
        print("Restarting game...")
        self.__init__()
    
    def show_help(self):
        """Display help information"""
        print("\n" + "="*40)
        print("STRATEGY GAME CONTROLS")
        print("="*40)
        print("Mouse:")
        print("  Left Click  - Select/Move units")
        print("  Right Click - Show unit info")
        print("\nKeyboard:")
        print("  SPACE    - Next turn")
        print("  L        - Restart game")
        print("  H        - Show help")
        print("  ESC      - Quit game")
        print("="*40 + "\n")
    
    def print_game_state(self):
        """Print debug information about game state"""
        print("\n" + "-"*30)
        print("GAME STATE DEBUG")
        print("-"*30)
        print(f"Current Player: {self.game_board.get_player_acting().getTeam()}")
        print(f"Board Size: {self.game_board.get_width()}x{self.game_board.get_height()}")
        print(f"Selected Tile: {self.game_board.get_selected_tile()}")
        
        # Count units
        p0_units = len(self.game_board.units_of_player(self.game_board.get_player_num(0)))
        p1_units = len(self.game_board.units_of_player(self.game_board.get_player_num(1)))
        print(f"Player 0 Units: {p0_units}")
        print(f"Player 1 Units: {p1_units}")
        print("-"*30 + "\n")
    
    def update_visuals(self):
        """Update all visual elements"""
        self.renderer.update_all()
    
    def render(self):
        """Render everything to screen"""
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        print("\nStarting Strategy Game...")
        self.show_help()
        
        try:
            while self.running:
                # Handle input
                self.handle_events()
                
                # Update visuals
                self.update_visuals()
                
                # Render to screen
                self.render()
                
                # Control frame rate
                self.clock.tick(FPS)
                
        except KeyboardInterrupt:
            print("\nGame interrupted by user")
        except Exception as e:
            print(f"Game error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def shutdown(self):
        """Initiate game shutdown"""
        print("Shutting down game...")
        self.running = False
    
    def cleanup(self):
        """Clean up resources"""
        pygame.quit()
        print("Game closed successfully")
        sys.exit()

def main():
    """Entry point"""
    try:
        game = StrategyGame()
        game.game_board.tiles_in_area(0, 6, 2)
        game.run()
    except Exception as e:
        print(f"Failed to start game: {e}")
        pygame.quit()
        sys.exit(1)

if __name__ == '__main__':
    main()
