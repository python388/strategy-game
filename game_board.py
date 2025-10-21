# game_board.py - Pure game logic, no pygame dependencies
import tile
import math
import statreader
import player
from collections import deque
import copy
import unit

class GameBoard:
    """Handles pure game logic - no rendering or pygame dependencies"""
    
    def __init__(self, width=10, height=20):
        self.width = width
        self.height = height
        self.turn_count = 1
        self.tiles = []
        self.selected_tile = None
        self.second_selected_tile = None
        self.targeted_tile = None
        self.player0 = player.Player(5, 0)
        self.player1 = player.Player(5, 1)
        self.player_acting = self.player0
        self.statreader = statreader
        self.click_state = 'nothing selected'
        self.building_tile = None
        
        # Initialize empty board
        for y in range(self.height):
            self.tiles.append([])
            for x in range(self.width):
                self.tiles[-1].append(tile.Tile(x, y))
    
    # ==========================================================================
    # CORE GAME LOGIC METHODS
    # ==========================================================================
    
    def tile_at(self, x, y):
        """Get tile at coordinates"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None
    
    def tile_from_coords(self, position, tile_dimensions):
        """Convert pixel coordinates to tile coordinates"""
        x = math.floor(position[0] / tile_dimensions)
        y = math.floor(position[1] / tile_dimensions)
        return self.tile_at(x, y)
    
    def initialize_unit(self, x: int, y: int, file_name: str, player_id: bool, tile_dimensions=40, prebuilt=False):
        """Add a unit to the board"""
        tile = self.tile_at(x, y)
        if tile:
            if player_id:
                tile.addUnit(statreader.unitFromStatsheet(file_name, self.player1, tile_dimensions, prebuilt=prebuilt))
            else:
                tile.addUnit(statreader.unitFromStatsheet(file_name, self.player0, tile_dimensions, prebuilt=prebuilt))
    
    def set_click_state(self):
        if not(self.selected_tile) or self.selected_tile.get_unit() == None:
            self.click_state = 'nothing selected'
        elif self.selected_tile.get_unit() != None:
            if self.selected_tile.get_unit().getPlayer() == self.player_acting:
                if self.second_selected_tile:
                    self.click_state = 'confirming movement'
                elif self.targeted_tile:
                    self.click_state = 'confirming attack'
                elif self.building_tile:
                    self.click_state = 'confirming build'
                elif self.click_state == 'producing unit or acting':
                    pass
                else:
                    self.click_state = 'choosing action'
            else:
                self.click_state = 'enemy unit selected'

    def process_tile_click(self, tile_clicked):
        """Process a tile click and return actions needed"""
        actions = []
        self.set_click_state()

        if self.click_state == 'confirming movement':
            if tile_clicked == self.second_selected_tile:
                actions.append(('move', self.selected_tile, self.second_selected_tile))
                self.move(self.selected_tile, self.second_selected_tile)
                self.selected_tile = self.second_selected_tile
                self.clear_tile_selection()
            else:
                self.choose_action(tile_clicked)
        elif self.click_state == 'confirming attack':
            if tile_clicked == self.targeted_tile:
                actions.append(('attack', self.selected_tile, self.targeted_tile))
                self.attack(self.selected_tile, self.targeted_tile)
                self.clear_tile_selection()
            else:
                self.choose_action(tile_clicked)
        elif self.click_state == 'confirming build':
            if tile_clicked == self.building_tile:
                actions.append(('build', self.selected_tile, self.building_tile))
                self.building_tile.get_unit().construct_tick()
                self.selected_tile.get_unit().do_action()
                self.clear_tile_selection()
            else:
                self.choose_action(tile_clicked)
        elif self.click_state == 'choosing action':
            self.choose_action(tile_clicked)
        elif self.click_state == 'producing unit or acting':
            if tile_clicked in self.empty_surrounding_tiles(self.selected_tile.get_x(), self.selected_tile.get_y()):
                self.production_function(self, tile_clicked.get_x(), tile_clicked.get_y())
            else:
                self.choose_action()
        else:
            self.clear_tile_selection()
            self.selected_tile = tile_clicked
        actions.append(('select', tile_clicked))
        
        return actions
    
    def move(self, start, destination):
        """Move a unit from start to destination"""
        if start.get_unit():
            start.get_unit().doMove()
            destination.addUnit(start.get_unit())
            start.removeUnit()
    
    def choose_action(self, tile_clicked):
        acted = 0
        if tile_clicked in self.moveable_tiles_from(self.selected_tile):
            self.clear_tile_selection
            self.second_selected_tile = tile_clicked
            acted = 1
        elif tile_clicked in self.attackable_tiles_from(self.selected_tile):
            self.clear_tile_selection
            self.targeted_tile = tile_clicked
            acted = 1
        elif 'builder' in self.selected_tile.get_unit().getTags():
            if tile_clicked in self.buildable_tiles_from(self.selected_tile) and self.selected_tile.get_unit().getAttacks() >= 1:
                self.clear_tile_selection
                self.building_tile = tile_clicked
                acted = 1
        if not(acted):
            self.selected_tile = tile_clicked
            self.clear_tile_selection()

    def attack(self, start, target):
        """Handle combat between units, including status effects"""
        if not(start.get_unit()):
            return
            
        if target.get_unit().getPlayer() != start.get_unit().getPlayer():
            # Calculate and apply damage
            damage = start.get_unit().damageTo(target.get_unit())
            target.damageUnit(damage)
            
            # Apply status effect on hit if the unit has one
            start.get_unit().apply_status_on_hit(target.get_unit())
            
            # Handle area damage
            if start.get_unit().getArea() > 0:
                for tile in self.tiles_with_enemy_units_in_area(target.get_x(), target.get_y(), start.get_unit().getArea()):
                    damage = start.get_unit().damageTo(tile.get_unit())
                    falloff = start.get_unit().getDamageFalloff() ** self.distance_between(target, tile)
                    tile.damageUnit(damage * falloff)
                    
                    # Apply status effects to area damage targets too
                    start.get_unit().apply_status_on_hit(tile.get_unit())

        start.get_unit().doAttack()
    
    def next_turn(self):
        """Advance to next turn"""
        self.second_selected_tile = None
        self.targeted_tile = None
        self.turn_count += 0.5

        # Process status effects and handle unit deaths FIRST
        units_to_remove = []
        for row in self.tiles:
            for square in row:
                if square.get_unit():
                    if square.get_unit().getPlayer() == self.player_acting:
                        # Process status effects first
                        unit_died = square.get_unit().process_status_effects()
                        if unit_died:
                            units_to_remove.append(square)
        
        # Remove units that died from status effects
        for square in units_to_remove:
            square.removeUnit()
        
        # THEN do normal turn processing (attacks, movement reset) for surviving units
        for row in self.tiles:
            for square in row:
                if square.get_unit():
                    # Reset attacks and movement without processing status effects again
                    square.get_unit().nextTurn()
        
        # Switch active player
        if self.player_acting == self.player0:
            self.player_acting = self.player1
        else:
            self.player_acting = self.player0
        
        # Process income
        self.do_income(self.player_acting)
    
    # ==========================================================================
    # MOVEMENT AND ATTACK LOGIC
    # ==========================================================================
    
    def moveable_tiles_from(self, start_tile):
        """Get all tiles a unit can move to"""
        move_options = []

        if start_tile.get_unit():
            possible_moves = self.get_reachable_squares(start_tile, start_tile.get_unit().getSpeed())
            if start_tile.get_unit().canMove() and start_tile.get_unit().getPlayer() == self.player_acting:
                for move in possible_moves:
                    square = self.tiles[move[1]][move[0]]
                    if square.occupiable() and square != start_tile:
                        if self.distance_between(start_tile, square) <= start_tile.get_unit().getSpeed():
                            move_options.append(square)
        
        return move_options
    
    def buildable_tiles_from(self, start_tile):
        build_options = []

        if start_tile.get_unit():
            possible_builds = self.surrounding_tiles(start_tile.get_x(), start_tile.get_y())
            for build in possible_builds:
                if build.get_unit():
                    if build.get_unit().is_under_construction() and build.get_unit().getPlayer() == self.player_acting:
                        build_options.append(build)
        
        return build_options

    def tiles_in_area(self, x, y, area):
        tiles = []

        for dx in range(-area, area + 1):
        # For a given dx, dy must satisfy |dx| + |dy| <= area -> |dy| <= area - |dx|
            max_dy = area - abs(dx)
            for dy in range(-max_dy, max_dy + 1):
                if dx == 0 and dy == 0:
                    continue
                new_x = x + dx
                new_y = y + dy

                if 0 <= new_x < self.width and 0 <= new_y < self.height:
                    tiles.append(self.tile_at(new_x, new_y))

        return tiles
    
    def tiles_with_enemy_units_in_area(self, x, y, area):
        enemy_units_tiles = []
        for tile in self.tiles_in_area(x, y, area):
            if tile.get_unit():
                if tile.get_unit().getPlayer() != self.player_acting:
                    enemy_units_tiles.append(tile)
        return enemy_units_tiles

    def attackable_tiles_from(self, start_tile):
        """Get all tiles a unit can attack"""
        attackable_squares = []
        
        if start_tile.get_unit():
            if start_tile.get_unit().getAttacks() and start_tile.get_unit().getPlayer() == self.player_acting:
                for row in self.tiles:
                    for tile in row:
                        if start_tile.get_unit() and tile.get_unit():
                            if (tile.get_unit().getPlayer() != start_tile.get_unit().getPlayer() and 
                                self.distance_between(start_tile, tile) <= start_tile.get_unit().getRange()):
                                attackable_squares.append(tile)
        
        return attackable_squares
    
    def get_reachable_squares(self, start, max_speed):
        """BFS to find all reachable squares within movement range"""
        rows = len(self.tiles)
        cols = len(self.tiles[0])
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        queue = deque([(start.get_x(), start.get_y(), 0)])
        visited = set()
        visited.add(start)
        reachable = []
        
        while queue:
            x, y, dist = queue.popleft()
            
            if dist <= max_speed:
                reachable.append((x, y))
            
            if dist >= max_speed:
                continue
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < cols and 0 <= ny < rows and 
                    self.move_throughable(self.tiles[ny][nx])):
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny, dist + 1))
        
        return reachable
    
    def distance_between(self, tile1, tile2):
        """Calculate Manhattan distance between tiles"""
        return abs(tile1.get_x() - tile2.get_x()) + abs(tile1.get_y() - tile2.get_y())
    
    def tiles_in_range(self, start_tile, range_val):
        """Generator for all tiles within range"""
        for row in self.tiles:
            for square in row:
                if self.distance_between(start_tile, square) <= range_val:
                    yield square
    
    def move_throughable(self, tile):
        """Check if a tile can be moved through"""
        return tile.moveThroughable(self.player_acting)
    
    # ==========================================================================
    # ECONOMIC SYSTEM
    # ==========================================================================
    
    def buy_unit(self, x, y, unit, dimensions):
        """Purchase and place a unit"""
        test_unit = statreader.unitFromStatsheet('statsheets/' + unit, self.player_acting)
        if self.player_acting.getMoney() >= test_unit.getCost():
            self.initialize_unit(x, y, 'statsheets/' + unit, self.player_acting.getTeam(), dimensions)
            self.player_acting.spendMoney(test_unit.getCost())
            return True
        else:
            del test_unit
            return False
    
    def do_income(self, player):
        """Calculate and apply income for a player"""
        income = 0
        for unit in self.units_of_player(player):
            if not(unit.is_under_construction()):
                income += unit.getProduction()
        player.makeIncome(income)
    


    def units_of_player(self, player: player.Player) -> list:
        """Get all units belonging to a player"""
        unit_list = []
        for y in self.tiles:
            for tile in y:
                if tile.get_unit():
                    if tile.get_unit().getPlayer() == player:
                        unit_list.append(tile.get_unit())
        return unit_list
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def surrounding_tiles(self, x, y):
        """Get all tiles surrounding a position"""
        directions = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        surrounding = []
        for direction in directions:
            tile = self.tile_at(x + direction[0], y + direction[1])
            if tile:
                surrounding.append(tile)
        return surrounding
    
    def clear_tile_selection(self):
        self.targeted_tile = None
        self.second_selected_tile = None
        self.building_tile = None

    def empty_surrounding_tiles(self, x, y):
        """Get all empty tiles surrounding a position"""
        return [tile for tile in self.surrounding_tiles(x, y) if tile.occupiable()]
    
    def production_function(self):
        pass

    def unit_production_functions_from(self, x, y, dimensions):
        """Get production functions for a tile (for UI)"""
        produceable_unit_functions = []
        empty_tiles = self.empty_surrounding_tiles(x, y)
        produceableUnits = self.statreader.units_with_tag(f'produced by {self.tile_at(x, y).get_unit().getName()}')

        for statsheet_name in produceableUnits:
            cost = self.statreader.cost_of(statsheet_name)
            name_label = statsheet_name[0:-4]

            if not empty_tiles:
                produceable_unit_functions.append((name_label + ' No Space', lambda: None))
            elif 'builder' in self.selected_tile.get_unit().getTags() and self.selected_tile.get_unit().getAttacks() == 0:
                produceable_unit_functions.append((name_label + ' No Action', lambda: None))
            elif self.player_acting.getMoney() < cost:
                produceable_unit_functions.append((f'{cost}: {name_label} - Insufficient Funds', lambda: None))
            else:
                def click_function(statsheet_name):
                    def production_function(self, x, y):
                        if self.buy_unit(x, y, statsheet_name, dimensions) and 'builder' in self.selected_tile.get_unit().getTags():
                            self.selected_tile.get_unit().do_action()
                        self.click_state = 'choosing action'
                    self.production_function = production_function
                    self.click_state = 'producing unit or acting'
                    self.clear_tile_selection()
                produceable_unit_functions.append((
                    f'{cost}: {name_label}', 
                    lambda sn=statsheet_name: click_function(sn)
                ))
        
        return produceable_unit_functions
    
    def hotkey_functions_from(self, x, y, dimensions):
        hotkey_functions = []
        empty_tiles = self.empty_surrounding_tiles(x, y)
        produceableUnits = self.statreader.units_with_tag(f'produced by {self.tile_at(x, y).get_unit().getName()}')
        
        for statsheet_name in produceableUnits:
            if not empty_tiles:
                pass
            elif 'builder' in self.selected_tile.get_unit().getTags() and self.selected_tile.get_unit().getAttacks() == 0:
                pass
            else:
                def click_function(statsheet_name):
                    def production_function(self, x, y):
                        if self.buy_unit(x, y, statsheet_name, dimensions) and 'builder' in self.selected_tile.get_unit().getTags():
                            self.selected_tile.get_unit().do_action()
                        self.click_state = 'choosing action'
                    self.production_function = production_function
                    self.click_state = 'producing unit or acting'
                    self.clear_tile_selection()
                hotkey_functions.append((
                    statreader.hotkey_of(statsheet_name),
                    lambda sn=statsheet_name: click_function(sn),
                    statsheet_name[0:-4]
                ))
        return hotkey_functions
    
    # ==========================================================================
    # GETTERS
    # ==========================================================================
    
    def get_width(self):
        return self.width
    
    def get_height(self):
        return self.height
    
    def get_player_acting(self):
        return self.player_acting
    
    def get_selected_tile(self):
        return self.selected_tile
    
    def get_second_selected_tile(self):
        return self.second_selected_tile
    
    def get_targeted_tile(self):
        return self.targeted_tile
    
    def get_player_num(self, num):
        return self.player1 if num else self.player0
    
    def get_click_state(self):
        return self.click_state
    
    def get_building_tile(self):
        return self.building_tile

    def get_turn(self):
        return self.turn_count
    
    def get_units(self) -> iter:
        for row in self.tiles:
            for tile in row:
                if tile.get_unit():
                    yield tile.get_unit()

    def tile_of_unit(self, unit: unit.Unit) -> None:
        for row in self.tiles:
            for tile in row:
                if tile.get_unit() == unit:
                    return tile