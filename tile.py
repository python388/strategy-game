from colors import COLORS

class Tile(object):
    def __init__(self, x, y, outline=COLORS.BLACK, unit=None):
        self.x = x
        self.y = y
        self.outline = outline
        self.unit = unit
        # active unit is for movement calculation (so a carried troop can move out of another troop)
        self.activeUnit = unit

    def getCords(self):
        return (self.x, self.y)

    def get_unit(self):
        return self.unit

    def removeUnit(self):
        self.unit = None

    def damageUnit(self, damage):
        if self.unit.takeDamage(damage):
            if len(self.unit.carrying) > 0:
                x = self.unit.carrying[0]
            else:
                x = False
            self.removeUnit()
            if x:
                self.addUnit(x)                            

    def moveThroughable(self, player):
        if self.get_unit():
            return self.unit.moveThroughable(player)
        else:
            return True
    
    #checks if a tile has a unit that can carry other units
    def canCarry(self, startingTile):
        if self.unit:
            if self.unit.carryCapacity != 0 and len(self.unit.carrying) < self.unit.carryCapacity and self.unit.player == startingTile.unit.player:
                return True
            else:
                return False
        else:
            return False
        
    def getCarriedUnits(self):
        return self.unit.carrying
    
    def tileEmpty(self):
        if self.unit == None:
            return True
        else: 
            return False 

    def addUnit(self, unit):
        self.unit = unit
        self.activeUnit = unit
        self.unit.set_tile(self)

    def getOutline(self):
        return self.outline

    def changeOutline(self, color):
        self.outline = color

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def getForeground(self):
        if self.unit:
            return self.unit.get_image()
        else:
            return None
    
    def set_active_unit(self, carriedIndex):
        self.ActiveUnit = self.get_unit().carried[carriedIndex]

    def get_active_unit(self):
        return self.activeUnit
