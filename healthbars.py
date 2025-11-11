import colors
import pygame

class Healthbar(object):
    def __init__(self, unit):
        self.unit = unit

    def draw_healthbar(self, screen, tiledimensions, unit):
        left = (self.unit.get_x() * tiledimensions) + (2 * tiledimensions)/16
        top = (self.unit.get_y() * tiledimensions) + (2 * tiledimensions)/16
        pygame.draw.rect(screen, colors.COLORS.RED, (left, top, tiledimensions * 0.75, tiledimensions * 0.10))
        pygame.draw.rect(screen, colors.COLORS.GREEN, (left, top, tiledimensions * (unit.getHp()/unit.getMaxHp()) * 0.75, tiledimensions * 0.10))