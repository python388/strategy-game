# Enhanced status_effects.py with simplified target restrictions

class Status_Effect(object):
    def __init__(self, name, target=None, duration=1, duration_stacking=True, stacking=False, 
                 self_damage=0, attack_change=0, armor_change=0, actions_change=0, 
                 range_change=0, area_change=0, damage_falloff_change=0, speed_change=0, 
                 special_behavior=None, special_behavior_trigger=None,
                 required_tags=None, immunity_tags=None):
        self.name = name
        self.duration = duration
        self.unit = target
        self.stacking = stacking
        self.self_damage = self_damage
        self.attack_change = attack_change
        self.armor_change = armor_change
        self.actions_change = actions_change
        self.range_change = range_change
        self.area_change = area_change
        self.damage_falloff_change = damage_falloff_change
        self.speed_change = speed_change
        self.special_behavior = special_behavior
        self.special_behavior_trigger = special_behavior_trigger
        self.duration_stacking = duration_stacking
        
        # Simplified target restriction system
        self.required_tags = required_tags or []  # Unit must have at least one of these tags
        self.immunity_tags = immunity_tags or []   # Units with these tags are immune to this effect

    def can_affect_target(self, target_unit):
        """Check if this status effect can be applied to the target unit"""
        target_tags = target_unit.getTags()
        
        # Check immunity tags first (highest priority)
        for immunity_tag in self.immunity_tags:
            if immunity_tag in target_tags:
                return False, f"{target_unit.getName()} is immune to {self.name} (has {immunity_tag} tag)"
        
        # Check required tags
        if self.required_tags:
            has_required = any(tag in target_tags for tag in self.required_tags)
            if not has_required:
                return False, f"{target_unit.getName()} cannot be affected by {self.name} (missing required tags: {self.required_tags})"
        
        return True, "Can apply effect"

    def set_duration(self, value):
        self.duration = value

    def add_duration(self, value):
        self.duration += value

    def decrease_duration(self, amount):
        self.duration -= amount
        if self.duration <= 0 and self.unit:
            self.unit.remove_status(self)

    # All existing getters...
    def get_name(self):
        return self.name
    
    def get_duration_stacking(self):
        return self.duration_stacking
    
    def get_duration(self):
        return self.duration
    
    def get_unit(self):
        return self.unit
    
    def get_stacking(self):
        return self.stacking
    
    def get_self_damage(self):
        return self.self_damage
    
    def get_attack_change(self):
        return self.attack_change
    
    def get_armor_change(self):
        return self.armor_change
    
    def get_actions_change(self):
        return self.actions_change
    
    def get_range_change(self):
        return self.range_change
    
    def get_area_change(self):
        return self.area_change
    
    def get_damage_falloff_change(self):
        return self.damage_falloff_change
    
    def get_speed_change(self):
        return self.speed_change
    
    def get_special_behavior(self):
        return self.special_behavior
    
    def get_special_behavior_trigger(self):
        return self.special_behavior_trigger

    # Updated getters for simplified restriction system
    def get_required_tags(self):
        return self.required_tags
    
    def get_immunity_tags(self):
        return self.immunity_tags


# Predefined status effects with simplified restrictions
class PoisonEffect(Status_Effect):
    def __init__(self, target=None, duration=3):
        super().__init__(
            name="Poison",
            target=target,
            duration=duration,
            duration_stacking=False,
            stacking=True,
            self_damage=2,
            required_tags=["alive"],  # Only affects living units
            immunity_tags=["poison_immune", "construct", "elemental"]
        )

class ArmorBreakEffect(Status_Effect):
    def __init__(self, target=None, duration=5):
        super().__init__(
            name="Armor Break",
            target=target,
            duration=duration,
            duration_stacking=True,
            stacking=False,
            armor_change=-2,
            immunity_tags=["armor_break_immune", "no_armor", "incorporeal"]  # Combined forbidden into immunity
        )

class SlowEffect(Status_Effect):
    def __init__(self, target=None, duration=3):
        super().__init__(
            name="Slow",
            target=target,
            duration=duration,
            duration_stacking=True,
            stacking=False,
            speed_change=-1,
            immunity_tags=["slow_immune", "teleporter", "immobile"]  # Can't slow immobile things
        )

class StunEffect(Status_Effect):
    def __init__(self, target=None, duration=1):
        super().__init__(
            name="Stun",
            target=target,
            duration=duration,
            duration_stacking=False,
            stacking=False,
            actions_change=-10,
            speed_change=-10,
            required_tags=["alive"],  # Only living things can be stunned
            immunity_tags=["stun_immune", "mindless", "construct"]
        )

class BerserkerRageEffect(Status_Effect):
    def __init__(self, target=None, duration=3):
        super().__init__(
            name="Berserker Rage",
            target=target,
            duration=duration,
            duration_stacking=False,
            stacking=False,
            attack_change=3,
            armor_change=-1,
            actions_change=1,
            required_tags=["alive"],  # Only living things can go berserk
            immunity_tags=["rage_immune", "calm", "mindless"]  # Mindless creatures can't rage
        )

class FreezeEffect(Status_Effect):
    def __init__(self, target=None, duration=2):
        super().__init__(
            name="Freeze",
            target=target,
            duration=duration,
            duration_stacking=True,
            stacking=False,
            speed_change=-2,
            actions_change=-1,
            immunity_tags=["fire", "freeze_immune", "hot_blooded"]
        )

class BurnEffect(Status_Effect):
    def __init__(self, target=None, duration=3):
        super().__init__(
            name="Burn",
            target=target,
            duration=duration,
            duration_stacking=True,
            stacking=True,  # Multiple burns can stack
            self_damage=1,
            armor_change=-1,  # Fire weakens armor
            immunity_tags=["fire_immune", "fire", "burn_immune", "incorporeal"]
        )

class FearEffect(Status_Effect):
    def __init__(self, target=None, duration=2):
        super().__init__(
            name="Fear",
            target=target,
            duration=duration,
            duration_stacking=False,
            stacking=False,
            attack_change=-2,
            speed_change=-1,
            required_tags=["alive"],
            immunity_tags=["fearless", "mindless", "construct"]
        )

class HealingEffect(Status_Effect):
    def __init__(self, target=None, duration=3):
        super().__init__(
            name="Regeneration",
            target=target,
            duration=duration,
            duration_stacking=True,
            stacking=False,
            self_damage=-2,  # Negative damage = healing
            required_tags=["alive"],
            immunity_tags=["construct"]  # These can't heal naturally
        )

class BlessedEffect(Status_Effect):
    def __init__(self, target=None, duration=4):
        super().__init__(
            name="Blessed",
            target=target,
            duration=duration,
            duration_stacking=True,
            stacking=False,
            attack_change=1,
            armor_change=1,
            required_tags=["alive"],
            immunity_tags=[]  # These can't be blessed
        )