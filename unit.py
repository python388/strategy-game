import math
from bonuses import *
from status_effects import *

class Unit(object):
    def __init__(self, name='None', attacks=1, attack=5, hp=10, armor=0, speed=3, range=1, 
                 cost=2, area=0, damageFalloff=0, bonuses=Bonuses(), tags='none', 
                 carryCapacity=0, production=0, image=None, player=0, hotkey='-', 
                 inProgress=True, buildcost=False, status_on_hit=None):
        self.name = name
        self.maxAttacks = attacks
        self.attacks = self.maxAttacks
        self.maxHp = hp
        self.hp = hp
        self.attack = attack
        self.armor = armor
        self.speed = speed
        self.area = area
        self.range = range
        self.cost = cost
        self.image = image
        self.damageFalloff = damageFalloff
        self.hasMoved = 0
        self.player = player
        self.bonuses = bonuses
        self.tags = tags
        self.image = image
        self.production = production
        self.hotkey = hotkey
        self.status_effects = []  # List to store active status effects
        self.status_on_hit = status_on_hit  # Status effect to apply when attacking
        
        if 'produced by builder' in self.tags:
            self.buildProgress = 1
            self.inProgress = inProgress
            if buildcost:
                self.buildCost = buildcost
            else:
                self.buildCost = self.cost
        else:
            self.inProgress = False

    def add_status_effect(self, status_effect):
        """Add a status effect to the unit"""
        # Check if this status effect can affect this unit
        can_affect, reason = status_effect.can_affect_target(self)
        if not can_affect:
            print(f"Status effect blocked: {reason}")
            return False
        
        status_effect.unit = self  # Set the target unit
        
        # Check if effect already exists and handle stacking
        existing_effect = None
        for effect in self.status_effects:
            if effect.get_name() == status_effect.get_name():
                existing_effect = effect
                break
        
        if existing_effect:
            if status_effect.get_stacking():
                # Allow multiple instances of the same effect
                self.status_effects.append(status_effect)
            elif status_effect.get_duration_stacking():
                # Add duration to existing effect
                existing_effect.add_duration(status_effect.get_duration())
            else:
                # Replace existing effect
                self.status_effects.remove(existing_effect)
                self.status_effects.append(status_effect)
        else:
            # No existing effect, just add it
            self.status_effects.append(status_effect)
        
        print(f"{status_effect.get_name()} applied to {self.name} for {status_effect.get_duration()} turns")
        return True

    def remove_status(self, status):
        """Remove a specific status effect"""
        if status in self.status_effects:
            self.status_effects.remove(status)

    def remove_status_by_name(self, effect_name):
        """Remove all status effects with the given name"""
        self.status_effects = [effect for effect in self.status_effects if effect.get_name() != effect_name]

    def get_status_effect_total(self, stat_name):
        """Calculate the total modifier for a given stat from all active status effects"""
        total = 0
        for effect in self.status_effects:
            if hasattr(effect, stat_name):
                total += getattr(effect, stat_name)
        return total

    def process_status_effects(self):
        """Process all status effects for one turn"""
        effects_to_remove = []
        
        for effect in self.status_effects:
            # Apply self damage/healing if any
            if effect.get_self_damage() != 0:
                if effect.get_self_damage() > 0:  # Damage
                    damage_taken = max(1, effect.get_self_damage() - self.getArmor())
                    self.hp -= damage_taken
                    print(f"{self.name} takes {damage_taken} {effect.get_name()} damage!")
                else:  # Healing (negative damage)
                    healing = abs(effect.get_self_damage())
                    old_hp = self.hp
                    self.hp = min(self.maxHp, self.hp + healing)
                    actual_healing = self.hp - old_hp
                    if actual_healing > 0:
                        print(f"{self.name} heals {actual_healing} HP from {effect.get_name()}!")
            
            # Decrement duration
            effect.decrease_duration(1)
            
            # Mark for removal if expired
            if effect.get_duration() <= 0:
                effects_to_remove.append(effect)
        
        # Remove expired effects
        for effect in effects_to_remove:
            self.remove_status(effect)
            print(f"{effect.get_name()} effect expired on {self.name}")
        
        # Check if unit died from status effects
        if self.hp <= 0:
            print(f"{self.name} died from status effects!")
            return True  # Indicate unit death
        return False

    def apply_status_on_hit(self, target):
        """Apply this unit's on-hit status effect to target"""
        if self.status_on_hit and hasattr(target, 'add_status_effect'):
            # Create a new instance of the status effect for the target
            effect = None
            if self.status_on_hit == "poison":
                effect = PoisonEffect(target=target)
            elif self.status_on_hit == "armor_break":
                effect = ArmorBreakEffect(target=target)
            elif self.status_on_hit == "slow":
                effect = SlowEffect(target=target)
            elif self.status_on_hit == "stun":
                effect = StunEffect(target=target)
            elif self.status_on_hit == "berserker_rage":
                effect = BerserkerRageEffect(target=target)
            elif self.status_on_hit == "freeze":
                effect = FreezeEffect(target=target)
            elif self.status_on_hit == "burn":
                effect = BurnEffect(target=target)
            elif self.status_on_hit == "fear":
                effect = FearEffect(target=target)
            elif self.status_on_hit == "regeneration":
                effect = HealingEffect(target=target)
            elif self.status_on_hit == "blessed":
                effect = BlessedEffect(target=target)
            else:
                print(f"Unknown status effect: {self.status_on_hit}")
                return False
            
            # Try to apply the effect (will check restrictions)
            success = target.add_status_effect(effect)
            if success:
                print(f"{self.name} applies {effect.get_name()} to {target.getName()}!")
            return success
        return False

    # Modified getters to include status effect modifiers
    def getRange(self):
        return max(0, self.range + self.get_status_effect_total('range_change'))
    
    def getAttacks(self):
        return max(0, self.attacks + self.get_status_effect_total('actions_change'))

    def getAttack(self):
        return max(0, self.attack + self.get_status_effect_total('attack_change'))

    def getArmor(self):
        return max(0, self.armor + self.get_status_effect_total('armor_change'))

    def getSpeed(self):
        if self.hasMoved:
            return 0
        else:
            return max(0, self.speed + self.get_status_effect_total('speed_change'))

    def getArea(self):
        return max(0, self.area + self.get_status_effect_total('area_change'))

    def getDamageFalloff(self):
        return max(0, self.damageFalloff + self.get_status_effect_total('damage_falloff_change'))

    # Status effect utility methods
    def has_status_effect(self, effect_name):
        """Check if unit has a specific status effect"""
        return any(effect.get_name() == effect_name for effect in self.status_effects)

    def get_status_effects_display(self):
        """Get a string representation of active status effects for UI"""
        if not self.status_effects:
            return ""
        
        effects_str = []
        for effect in self.status_effects:
            effects_str.append(f"{effect.get_name()}({effect.get_duration()})")
        
        return ", ".join(effects_str)

    # All your existing methods remain the same...
    def get_build_cost(self):
        return self.buildCost
    
    def get_build_progress(self):
        return self.buildProgress
    
    def is_under_construction(self):
        return self.inProgress
    
    def construct_tick(self):
        self.buildProgress += 1
        if self.buildProgress == self.cost:
            self.inProgress = False
    
    def getProduction(self):
        return self.production

    def getCost(self):
        return self.cost

    def getTags(self):
        return self.tags

    def getBonuses(self):
        return self.bonuses

    def getName(self):
        return self.name

    def getMaxHp(self):
        return self.maxHp

    def takeDamage(self, damage):
        self.hp -= max(round(damage) - self.getArmor(), 1)
        if self.hp <= 0:
            return True
        else:
            return False

    def getStatsheetName(self):
        return f'{self.name.title()}.txt'

    def damageTo(self, target):
        return self.getAttack() * self.bonuses.bonusAgainst(target)

    def moveThroughable(self, player):
        if self.player == player and not('obstructs movement' in self.tags):
            return True
        else:
            return False
    
    def getPlayer(self):
        return self.player

    def getImage(self):
        return self.image

    def doAttack(self):
        self.attacks -= 1

    def do_action(self):
        self.attacks -= 1

    def canAttack(self):
        return self.getAttacks() > 0

    def getHp(self):
        return self.hp

    def canMove(self):
        return not(self.hasMoved) and self.getSpeed() > 0

    def doMove(self):
        self.hasMoved = 1

    def nextTurn(self):
        self.attacks = self.maxAttacks
        self.hasMoved = 0
        
    def setPlayer(self, player):
        self.player = player