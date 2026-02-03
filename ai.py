"""Heuristic AI controller for strategy-game with improved tactics

Enhanced heuristic rules:
- For each unit owned by the AI this turn:
  - If on a center objective tile, hold position (attack or defend, don't move away)
  - If it can attack, choose target that:
    1. Takes bonus damage from this unit's bonuses
    2. Is weakest (lowest HP fraction)
    3. Is closest to center objective (mines) if tied
  - Else if it can move:
    1. Priority: move toward unoccupied center objectives
    2. Fallback: move toward nearest enemy
  - Else if it is a factory, spawn varied units:
    1. Rotate through cost brackets for diversity (cheap, mid, expensive)
    2. Fallback: pick cheapest affordable
- After finishing actions, call `board.next_turn()` to end the AI's turn
"""
import random
import mines

class HeuristicAI:
    def __init__(self, player):
        self.player = player
        # Track unit production by cost tier for variety
        self.production_history = []
        # Mine/objective coordinates
        self.center_objectives = set(mines.mineCoords)

    def _is_on_center(self, tile):
        """Check if a tile is a center objective"""
        return (tile.get_x(), tile.get_y()) in self.center_objectives

    def _center_distance(self, tile):
        """Return closest distance from tile to any center objective"""
        if not self.center_objectives:
            return float('inf')
        return min(abs(tile.get_x() - cx) + abs(tile.get_y() - cy) 
                   for cx, cy in self.center_objectives)

    def _get_unoccupied_centers(self, board):
        """Get center tiles that don't have an enemy unit"""
        unoccupied = []
        for cx, cy in self.center_objectives:
            tile = board.tile_at(cx, cy)
            if tile:
                # Occupy if empty or has our unit
                if not tile.get_unit() or tile.get_unit().getPlayer() == self.player:
                    unoccupied.append(tile)
        return unoccupied

    def _score_target(self, tile, attacking_unit, board):
        """Score a target tile for attack priority (higher = better target)
        
        Prioritizes:
        1. Bonus damage dealt
        2. Lowest HP fraction (damaged units)
        3. Closest to center objective
        """
        target_unit = tile.get_unit()
        if not target_unit:
            return -float('inf')
        
        # 1) Bonus multiplier (higher is better)
        bonus = attacking_unit.getBonuses().bonusAgainst(target_unit)
        
        # 2) Fractional HP (lower is better, so negate)
        frac_hp = target_unit.getHp() / max(1, target_unit.getMaxHp())
        
        # 3) Distance to center objective (closer is better, so negate)
        center_dist = self._center_distance(tile)
        
        # Combined score: prioritize by bonus, then by damage, then by position
        score = (bonus, -frac_hp, -center_dist)
        return score

    def _select_unit_to_produce(self, board, produceable, available_funds):
        """Choose a unit with cost-bracket diversity to avoid archer spam
        
        Strategy:
        1. Categorize units by cost: cheap (<3), mid (3-4), expensive (5+)
        2. Rotate through brackets for variety
        3. Fall back to cheapest if needed
        """
        if not produceable:
            return None
        
        # Categorize by cost
        costs = {s: board.statreader.cost_of(s) for s in produceable}
        affordable = {s: c for s, c in costs.items() if c <= available_funds}
        
        if not affordable:
            return None
        
        # Bucket into cost tiers
        cheap = [s for s, c in affordable.items() if c <= 2]
        mid = [s for s, c in affordable.items() if 3 <= c <= 4]
        expensive = [s for s, c in affordable.items() if c >= 5]
        
        # Use production history to rotate through brackets
        # Count recent units by tier
        recent_history = self.production_history[-5:] if self.production_history else []
        cheap_count = sum(1 for s in recent_history if costs.get(s, 0) <= 2)
        mid_count = sum(1 for s in recent_history if 3 <= costs.get(s, 0) <= 4)
        expensive_count = sum(1 for s in recent_history if costs.get(s, 0) >= 5)
        
        # Pick the bracket with fewest recent units
        buckets = []
        if cheap:
            buckets.append((cheap_count, cheap))
        if mid:
            buckets.append((mid_count, mid))
        if expensive:
            buckets.append((expensive_count, expensive))
        
        if not buckets:
            return None
        
        # Sort by count (pick underrepresented bracket)
        buckets.sort(key=lambda x: x[0])
        chosen_bucket = buckets[0][1]
        chosen = random.choice(chosen_bucket)
        
        self.production_history.append(chosen)
        return chosen

    def take_turn(self, board):
        """Execute one turn of AI actions"""
        units = list(board.units_of_player(self.player))
        random.shuffle(units)
        
        # Gather enemy units for analysis
        enemies = [e for e in board.get_units() if e.getPlayer() != self.player]
        # Get unoccupied center tiles
        unoccupied_centers = self._get_unoccupied_centers(board)

        for u in units:
            tile = board.tile_of_unit(u)
            if not tile:
                continue
            
            if u.is_under_construction():
                continue

            # Special: if on center tile, prefer to stay and defend/attack
            if self._is_on_center(tile):
                # Try to attack first
                if u.canAttack():
                    attackable = board.attackable_tiles_from(tile)
                    if attackable:
                        best = max(attackable, key=lambda t: self._score_target(t, u, board))
                        board.attack(tile, best)
                        continue
                # Don't move away from center unless no other choice
                continue

            # 1) Attack with bonus optimization
            if u.canAttack():
                attackable = board.attackable_tiles_from(tile)
                if attackable:
                    best = max(attackable, key=lambda t: self._score_target(t, u, board))
                    board.attack(tile, best)
                    continue

            # 2) Move toward unoccupied center objectives or engage enemy
            if u.canMove():
                moves = board.moveable_tiles_from(tile)
                if moves:
                    # Priority 1: Move toward unoccupied center if any exist
                    if unoccupied_centers:
                        best = min(moves, key=lambda sq: min(
                            board.distance_between(sq, ct) for ct in unoccupied_centers))
                    else:
                        # Priority 2: Move toward nearest enemy
                        if enemies:
                            enemy_tiles = [board.tile_of_unit(e) for e in enemies if board.tile_of_unit(e)]
                            if enemy_tiles:
                                best = min(moves, key=lambda sq: min(
                                    board.distance_between(sq, et) for et in enemy_tiles))
                            else:
                                best = moves[0]
                        else:
                            # No enemies, move to nearest center
                            best = min(moves, key=lambda sq: self._center_distance(sq))
                    
                    board.move(tile, best)
                    continue

            # 3) Produce varied units from factories
            if 'factory' in u.getTags():
                empty = board.empty_surrounding_tiles(tile.get_x(), tile.get_y())
                if empty:
                    produceable = board.statreader.units_with_tag(f'produced by {u.getName()}')
                    chosen = self._select_unit_to_produce(board, produceable, 
                                                          self.player.getMoney())
                    if chosen:
                        coords = empty[0]
                        board.buy_unit(coords.get_x(), coords.get_y(), chosen, 30)

        # End the AI player's turn
        try:
            board.next_turn()
        except RecursionError:
            print("AI aborted due to recursion depth")
