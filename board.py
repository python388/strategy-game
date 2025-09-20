# Updated board.py - Combines both classes for backward compatibility
from game_board import GameBoard
from board_renderer import BoardRenderer

class Board:
    """Combined class that maintains backward compatibility"""
    
    def __init__(self, produceable_units, width=10, height=20, tile_dimensions=40):
        self.game_board = GameBoard(produceable_units, width, height)
        self.renderer = BoardRenderer(self.game_board, tile_dimensions)
    
    # Delegate methods to appropriate classes
    def clickTile(self, pos):
        return self.renderer.handle_click(pos)
    
    def updateAll(self):
        return self.renderer.update_all()
    
    def initializeUnit(self, x, y, fileName, player):
        return self.game_board.initialize_unit(x, y, fileName, player, self.renderer.tile_dimensions)
    
    def nextTurn(self):
        return self.game_board.next_turn()
    
    def getPlayerNum(self, num):
        return self.game_board.get_player_num(num)
    
    def getWindow(self):
        return self.renderer.get_window()
    
    # Add more delegation methods as needed...