"""Heuristic AI controller for strategy-game with improved tactics

Enhanced heuristic rules:
- For each unit owned by the AI this turn:
  - If on a center objective tile, hold position (attack or defend, don't move away)
  - If it can attack, choose target that:
    1. Takes bonus damage from this unit's bonuses
    2. Is weakest (lowest HP fraction)
    3. Is closest to center objective (mines) if tied
  - Else if it is a builder:
    1. If not losing/desperate, try to build farms to match player's farm count
    2. Build only in safe locations (away from enemy units)
    3. Otherwise, move builder to front or defend
  - Else if it can move:
    1. If in danger (outnumbered), move away from enemy
    2. Priority: move toward unoccupied center objectives
    3. Fallback: move toward nearest enemy
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

    def _count_farms(self, board, player):
        """Count how many farms a player has"""
        farm_count = 0
        for unit in board.units_of_player(player):
            if 'producer' in unit.getTags():
                farm_count += 1
        return farm_count

    def _count_total_hp(self, board, player):
        """Calculate total HP of all units for a player"""
        total_hp = 0
        for unit in board.units_of_player(player):
            if not unit.is_under_construction():
                total_hp += unit.getHp()
        return total_hp

    def _is_in_dire_position(self, board):
        """Check if AI is in a dire position (losing/desperate)
        
        Returns True if:
        - Enemy has significantly more total HP
        - AI has very few units (< 2) and no farms
        """
        ai_units = [u for u in board.units_of_player(self.player) 
                    if not u.is_under_construction()]
        enemy_units = [u for u in board.get_units() 
                       if u.getPlayer() != self.player and not u.is_under_construction()]
        
        ai_farms = self._count_farms(board, self.player)
        enemy_farms = self._count_farms(board, [e for e in board.get_units() 
                                               if e.getPlayer() != self.player][0].getPlayer() 
                                        if board.get_units() else self.player)
        
        # Dire if very few combat units and no farms
        if len(ai_units) < 2 and ai_farms == 0:
            return True
        
        # Dire if severely outnumbered in total HP
        ai_hp = self._count_total_hp(board, self.player)
        enemy_hp = sum(u.getHp() for u in enemy_units)
        
        if enemy_hp > 0 and ai_hp < enemy_hp * 0.3:
            return True
        
        return False

    def _find_safe_build_location(self, board, builder_tile, enemy_units):
        """Find a safe adjacent tile to build a farm
        
        Safe means not adjacent to enemy units
        """
        builder_x, builder_y = builder_tile.get_x(), builder_tile.get_y()
        empty_tiles = board.empty_surrounding_tiles(builder_x, builder_y)
        
        # Filter to tiles not adjacent to enemies
        safe_tiles = []
        for tile in empty_tiles:
            is_safe = True
            tile_x, tile_y = tile.get_x(), tile.get_y()
            for enemy in enemy_units:
                enemy_tile = board.tile_of_unit(enemy)
                if enemy_tile:
                    # Distance of 1 means adjacent, distance of 2+ is safe
                    if board.distance_between(tile, enemy_tile) <= 1:
                        is_safe = False
                        break
            if is_safe:
                safe_tiles.append(tile)
        
        return safe_tiles

    def _is_likely_to_die(self, board, tile, unit):
        """Assess if a unit is likely to die if it stays on its current tile
        
        Considers:
        - Enemy units that can attack this tile
        - Total damage they can deal
        - Unit's current HP and armor
        - Whether unit can attack back
        """
        enemies_that_can_attack = []
        
        # Find all enemy units that can attack this tile
        for enemy in board.get_units():
            if enemy.getPlayer() != self.player:
                enemy_tile = board.tile_of_unit(enemy)
                if enemy_tile and enemy.canAttack():
                    # Check if enemy can attack this tile
                    attackable = board.attackable_tiles_from(enemy_tile)
                    if tile in attackable:
                        enemies_that_can_attack.append(enemy)
        
        if not enemies_that_can_attack:
            return False
        
        # Calculate total potential damage (each enemy deals max(1, attack - armor))
        total_damage = 0
        for enemy in enemies_that_can_attack:
            bonus = enemy.getBonuses().bonusAgainst(unit)
            base_damage = enemy.getAttack() * bonus
            damage_after_armor = max(1, base_damage - unit.getArmor())
            total_damage += damage_after_armor
        
        remaining_hp = unit.getHp() - total_damage
        
        # Unit is likely to die if it would be left with very low HP or dead
        # Also consider if unit can attack back to reduce the threat
        can_attack_back = len(board.attackable_tiles_from(tile)) > 0
        
        # If unit can attack back, be more willing to risk staying (higher threshold)
        # If unit cannot attack back, be more conservative (lower threshold)
        hp_threshold = 0.4 if can_attack_back else 0.7  # 40% vs 70% HP threshold
        
        return remaining_hp <= (unit.getMaxHp() * hp_threshold)

    def _find_retreat_tile(self, board, current_tile, enemies):
        """Find a safe tile to retreat to, preferring center tiles if possible"""
        moves = board.moveable_tiles_from(current_tile)
        if not moves:
            return None
        
        # Score retreat options
        retreat_options = []
        for move_tile in moves:
            # Calculate distance to nearest enemy
            enemy_distances = []
            for enemy in enemies:
                enemy_tile = board.tile_of_unit(enemy)
                if enemy_tile:
                    enemy_distances.append(board.distance_between(move_tile, enemy_tile))
            
            min_enemy_dist = min(enemy_distances) if enemy_distances else float('inf')
            
            # Prefer center tiles, then distance from enemies
            is_center = self._is_on_center(move_tile)
            score = (is_center, min_enemy_dist)
            retreat_options.append((score, move_tile))
        
        if retreat_options:
            # Sort by score (center first, then enemy distance)
            retreat_options.sort(key=lambda x: x[0], reverse=True)
            return retreat_options[0][1]
        
        return None

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
        
        # Check if we're in a losing position
        in_dire_position = self._is_in_dire_position(board)
        
        # Count farms for both players to determine if we should build more
        ai_farms = self._count_farms(board, self.player)
        enemy_player = self._get_enemy_player(board)
        enemy_farms = self._count_farms(board, enemy_player) if enemy_player else 0
        
        # Determine if we should be building farms (not if desperate)
        should_build_farms = not in_dire_position and ai_farms < enemy_farms + 1

        for u in units:
            tile = board.tile_of_unit(u)
            if not tile:
                continue
            
            if u.is_under_construction():
                continue

            # Special: if on center tile, prefer to stay and defend/attack
            if self._is_on_center(tile):
                # Assess if staying here is too dangerous
                if self._is_likely_to_die(board, tile, u):
                    # Unit is likely to die - attack if possible, otherwise retreat
                    if u.canAttack():
                        attackable = board.attackable_tiles_from(tile)
                        if attackable:
                            # Attack the most threatening enemy
                            best = max(attackable, key=lambda t: self._score_target(t, u, board))
                            board.attack(tile, best)
                            continue
                    
                    # Can't attack or no targets - retreat to safety
                    retreat_tile = self._find_retreat_tile(board, tile, enemies)
                    if retreat_tile:
                        board.move(tile, retreat_tile)
                        continue
                    # No safe retreat - stay and fight
                    if u.canAttack():
                        attackable = board.attackable_tiles_from(tile)
                        if attackable:
                            best = max(attackable, key=lambda t: self._score_target(t, u, board))
                            board.attack(tile, best)
                            continue
                else:
                    # Safe to stay - attack if possible, otherwise hold position
                    if u.canAttack():
                        attackable = board.attackable_tiles_from(tile)
                        if attackable:
                            best = max(attackable, key=lambda t: self._score_target(t, u, board))
                            board.attack(tile, best)
                            continue
                # Don't move away from center unless retreating from danger
                continue

            # Special handling for builders
            if 'builder' in u.getTags():
                # Builders should attack first if they can
                if u.canAttack():
                    attackable = board.attackable_tiles_from(tile)
                    if attackable:
                        best = max(attackable, key=lambda t: self._score_target(t, u, board))
                        board.attack(tile, best)
                        continue
                
                # Try to build farms if not in dire position and behind on farms
                if should_build_farms and u.getAttacks() >= 1:
                    safe_tiles = self._find_safe_build_location(tile, enemies)
                    if safe_tiles:
                        # Try to build a farm
                        for safe_tile in safe_tiles:
                            # Check if we can afford a farm
                            farm_cost = board.statreader.cost_of('Farm.txt')
                            if self.player.getMoney() >= farm_cost:
                                # Place farm unit on the safe tile
                                board.buy_unit(safe_tile.get_x(), safe_tile.get_y(), 'Farm.txt', 30)
                                u.do_action()  # Consume the builder's action
                                continue
                
                # If not building farms or can't, still move builders appropriately
                if u.canMove() and not in_dire_position:
                    # Move builder toward unoccupied centers
                    moves = board.moveable_tiles_from(tile)
                    if moves:
                        if unoccupied_centers:
                            best = min(moves, key=lambda sq: min(
                                board.distance_between(sq, ct) for ct in unoccupied_centers))
                        else:
                            # No centers, find a safe spot
                            best = min(moves, key=lambda sq: min(
                                (board.distance_between(sq, board.tile_of_unit(e)) for e in enemies 
                                 if board.tile_of_unit(e)), default=float('inf')))
                        board.move(tile, best)
                continue

            # 1) Attack with bonus optimization
            if u.canAttack():
                attackable = board.attackable_tiles_from(tile)
                if attackable:
                    best = max(attackable, key=lambda t: self._score_target(t, u, board))
                    board.attack(tile, best)
                    continue

            # 2) Move toward objectives or engage enemy (with avoidance logic)
            if u.canMove():
                moves = board.moveable_tiles_from(tile)
                if moves:
                    # If in dire position, move away from enemies
                    if in_dire_position and enemies:
                        enemy_tiles = [board.tile_of_unit(e) for e in enemies if board.tile_of_unit(e)]
                        if enemy_tiles:
                            # Choose move that maximizes distance from nearest enemy
                            best = max(moves, key=lambda sq: min(
                                board.distance_between(sq, et) for et in enemy_tiles))
                        else:
                            best = moves[0]
                    else:
                        # Normal behavior: move toward objectives or enemies
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
