# board_renderer.py - Visual rendering, all pygame code
import pygame
import math
from colors import COLORS
import UI
import game_board

class BoardRenderer:
    """Handles all visual rendering of the game board"""
    
    def __init__(self, game_board, tile_dimensions=40):
        pygame.init()
        self.game_board = game_board
        self.tile_dimensions = tile_dimensions
        
        # Calculate window size
        board_width = self.tile_dimensions * game_board.get_width()
        ui_width = 5 * self.tile_dimensions
        window_width = board_width + ui_width
        window_height = self.tile_dimensions * game_board.get_height()
        
        self.window = pygame.display.set_mode((window_width, window_height))
        
        # Initialize UI
        self.UI = UI.UI(
            board_width,
            self.window, 
            420,
            65,
            UI.Button(
                x=20,
                y=20,
                width=100, 
                height=20,
                label="next turn",
                eventWhenClick=self.game_board.next_turn
            )
        )
    
    def handle_click(self, pos):
        """Handle mouse clicks - returns True if handled by UI"""
        if pos[0] > self.game_board.get_width() * self.tile_dimensions:
            self.UI.doClick(pos)
            return True
        else:
            tile_clicked = self.tile_from_coords(pos)
            if tile_clicked:
                self.game_board.process_tile_click(tile_clicked)
            return False
    
    def tile_from_coords(self, position):
        """Convert screen coordinates to tile"""
        return self.game_board.tile_from_coords(position, self.tile_dimensions)
    
    def update_all(self):
        """Update all visual elements"""
        self.reset_tiles()
        self.generate_production_actions()
        self.UI.drawButtons()
        self.highlight_moveable_tiles()
        self.highlight_attackable_tiles()
        self.highlight_produceable_tiles()
        self.highlight_buildeable_tiles()
        self.color_tiles()
        self.UI.showPlayerInfo(self.game_board.get_player_acting())
        self.UI.displayHotkeys()
        self.UI.display_turn_count(self.game_board.get_turn())
    
    def reset_tiles(self):
        """Clear the screen and reset tile colors"""
        self.window.fill(COLORS.DGREEN)
        for row in self.game_board.tiles:
            for square in row:
                self.change_color(COLORS.BLACK, square)
    
    def color_tiles(self):
        """Apply colors to special tiles and render everything"""
        selected = self.game_board.get_selected_tile()
        second_selected = self.game_board.get_second_selected_tile()
        targeted = self.game_board.get_targeted_tile()
        building = self.game_board.get_building_tile()

        if selected:
            self.change_color(COLORS.RED, selected)
            if selected.getUnit():
                self.UI.displayStats(selected.getUnit())

        if building:
            self.change_color(COLORS.GREEN, building)
        
        if second_selected:
            color = COLORS.GREEN if second_selected.occupiable() else COLORS.RED
            self.change_color(color, second_selected)
        
        if targeted:
            self.change_color(COLORS.YELLOW, targeted)
        
        # Render all tiles
        for row in self.game_board.tiles:
            for square in row:
                self.update_image(square)
                self.draw_tile(square.getOutline(), square)
    
    def highlight_moveable_tiles(self):
        """Highlight tiles the selected unit can move to"""
        selected = self.game_board.get_selected_tile()
        if selected:
            for tile in self.game_board.moveable_tiles_from(selected):
                self.highlight_tile(tile, COLORS.LBLUE)

    def highlight_buildeable_tiles(self):
        selected = self.game_board.get_selected_tile()
        if selected:
            if selected.getUnit():
                if 'builder' in selected.getUnit().getTags() and selected.getUnit().getAttacks() >= 1:
                    for tile in self.game_board.buildable_tiles_from(selected):
                        self.highlight_tile(tile, COLORS.BLUE)
    
    def highlight_attackable_tiles(self):
        """Highlight tiles the selected unit can attack"""
        selected = self.game_board.get_selected_tile()
        if selected:
            for tile in self.game_board.attackable_tiles_from(selected):
                self.highlight_tile(tile, COLORS.RED)

    def highlight_produceable_tiles(self):
        if self.game_board.get_click_state() == 'producing unit or acting':
            for tile in self.game_board.empty_surrounding_tiles(self.game_board.selected_tile.getX(), self.game_board.selected_tile.getY()):
                self.highlight_tile(tile, COLORS.BLUE)
    
    def generate_production_actions(self):
        """Generate UI buttons based on game state"""
        self.UI.clearButtons()
        selected = self.game_board.get_selected_tile()
        if (selected and selected.getUnit() and 
            'factory' in selected.getUnit().getTags() and 
            selected.getUnit().getPlayer() == self.game_board.get_player_acting()):
            
            production_functions = self.game_board.unit_production_functions_from(
                selected.getX(), selected.getY()
            )
            self.UI.generateButtons(*production_functions)
            self.UI.generateHotkeys(*self.game_board.hotkey_functions_from(selected.getX(), selected.getY()))
        self.generate_build_actions()
    
    def generate_build_actions(self):
        selected = self.game_board.get_selected_tile()
        if (selected and selected.getUnit() and 
            'builder' in selected.getUnit().getTags() and 
            selected.getUnit().getPlayer() == self.game_board.get_player_acting()):
            
            production_functions = self.game_board.unit_production_functions_from(
                selected.getX(), selected.getY()
            )
            self.UI.generateButtons(*production_functions)
            self.UI.generateHotkeys(*self.game_board.hotkey_functions_from(selected.getX(), selected.getY()))
    
    # ==========================================================================
    # DRAWING METHODS
    # ==========================================================================
    
    def change_color(self, color, tile):
        """Change a tile's outline color"""
        tile.changeOutline(color)
    
    def draw_tile(self, color, tile):
        """Draw a tile with the specified color"""
        self.change_color(color, tile)
        rect = (
            tile.getX() * self.tile_dimensions,
            tile.getY() * self.tile_dimensions,
            self.tile_dimensions,
            self.tile_dimensions
        )
        pygame.draw.rect(self.window, tile.getOutline(), rect, 1)
    
    def highlight_tile(self, tile, color):
        """Highlight a tile with a color"""
        self.change_color(color, tile)
    
    def update_image(self, tile):
        """Draw unit image on tile if present"""
        if tile.getUnit():
            self.move_image(tile.getForeground(), tile.getX(), tile.getY())
    
    def move_image(self, image, x, y):
        """Blit an image to the screen at tile coordinates"""
        if image:
            screen_x = self.tile_dimensions * x
            screen_y = self.tile_dimensions * y
            self.window.blit(image, (screen_x, screen_y))
    
    def get_window(self):
        """Get the pygame window surface"""
        return self.window