from colors import COLORS

class Tile(object):
    def __init__(self, x, y, outline=COLORS.BLACK, unit=None):
        self.x = x
        self.y = y
        self.outline = outline
        self.unit = unit

    def getCords(self):
        return (self.x, self.y)

    def get_unit(self):
        return self.unit

    def removeUnit(self):
        self.unit = None

    def damageUnit(self, damage):
        if self.unit.takeDamage(damage):
            self.removeUnit()

    def moveThroughable(self, player):
        if self.get_unit():
            return self.unit.moveThroughable(player)
        else:
            return True
    
    def occupiable(self):
        if self.unit == None:
            return True
        else:
            return False

    def addUnit(self, unit):
        self.unit = unit
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
