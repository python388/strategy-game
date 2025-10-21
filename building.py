import bonuses
import unit

class Building(unit.Unit):
    def __init__(self, name='None', attacks=1, attack=5, hp=10, armor=0, speed=3, range=1, 
                 cost=2, area=0, damageFalloff=0, bonuses=bonuses.Bonuses(), tags='none', 
                 carryCapacity=0, production=0, image=None, player=0, hotkey='-', 
                 inProgress=True, buildcost=True, status_on_hit=None):
        super().__init__(name, attacks, attack, hp, armor, speed, range, 
                         cost, area, damageFalloff, bonuses, tags, 
                         carryCapacity, production, image, player, hotkey, 
                         inProgress, buildcost, status_on_hit)
        self.build_cost = buildcost


    def is_building(self):
        return True