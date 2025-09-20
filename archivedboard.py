import tile
import pygame
import math
from colors import COLORS
import statreader
import UI
from collections import deque
import player
import copy

class Board(object):
                    
    def __init__(self, produceableUnits):
        pygame.init()
        self.width = 10
        self.height = 20
        self.tileDimensions = 40
        self.window = pygame.display.set_mode((self.tileDimensions * self.width + 5 * self.tileDimensions, self.tileDimensions * self.height))
        self.tiles = []
        self.clock = pygame.time.Clock()
        self.window.fill(COLORS.DGREEN)
        self.selectedTile = None
        self.secondSelectedTile = None
        self.targetedTile = None
        self.player0 = player.Player(5, 0)
        self.player1 = player.Player(5, 1)
        self.playerActing = self.player0
        self.UI = UI.UI(
            self.tileDimensions * self.width,
            self.window, 
            420,
            65,
            UI.Button(
                x=20,
                y=20,
                width=100, 
                height=20,
                label="next turn",
                eventWhenClick=self.nextTurn
            )
        )
        
        for y in range(self.height):
            self.tiles.append([])
            for x in range(self.width):
                self.tiles[-1].append(tile.Tile(x, y, outline=COLORS.BLACK))
        
        self.produceableUnits = produceableUnits

    def addUnit(self, x, y, unit):
        self.tileAt(x, y).addUnit(unit, player)

    def showStats(self):
        selectedUnit = self.selectedTile.getUnit()
        self.UI.displayHealth(selectedUnit.getHp())

    def initializeUnit(self, x, y, fileName, player):
        if player:
            self.tileAt(x, y).addUnit(statreader.unitFromStatsheet(fileName, self.player1, self.tileDimensions))
        else:
            self.tileAt(x, y).addUnit(statreader.unitFromStatsheet(fileName, self.player0, self.tileDimensions))

    def clickTile(self, pos):
        if pos[0] > self.width * self.tileDimensions:
            self.UI.doClick(pos)
        else:
            tileClicked = self.tileFromCoords(pos) 
            if tileClicked == self.secondSelectedTile:
                self.move(self.selectedTile, self.secondSelectedTile)
                self.selectedTile = None
                self.secondSelectedTile = None
            elif tileClicked == self.targetedTile:
                self.attack(self.selectedTile, self.targetedTile)
                self.targetedTile = None
            else:
                self.selectTile(pos)

    def selectTile(self, position):
        tilePicked = self.tileFromCoords(position)
        if self.selectedTile:
            if self.selectedTile.getUnit():
                if tilePicked in self.moveableTilesFrom(self.selectedTile):
                    self.secondSelectedTile = tilePicked
                elif tilePicked in self.attackableTilesFrom(self.selectedTile):
                    self.targetedTile = tilePicked
                else:
                    self.selectedTile = tilePicked
                    self.targetedTile = None
                    self.secondSelectedTile = None
            else:
                self.secondSelectedTile = None
                self.targetedTile = None
                self.selectedTile = self.tileFromCoords(position)
        else:
            self.selectedTile = tilePicked
            self.targetedTile = None
            self.secondSelectedTile = None

    def tileAt(self, x, y):
        return self.tiles[y][x]

    def move(self, start, destination):
        start.getUnit().doMove()
        destination.addUnit(start.getUnit())
        start.removeUnit()

    def moveImage(self, image, x, y):
        self.window.blit(image, (self.tileDimensions * x, self.tileDimensions * y))

    def updateAll(self) -> None:
        self.resetTiles()
        self.generateButtons()
        self.UI.drawButtons()
        self.highlightMoveableTiles(self.selectedTile)
        self.highlightAttackableTiles(self.selectedTile)
        self.colorTiles()
        self.UI.showPlayerInfo(self.playerActing)
        
    def colorTiles(self):
        if self.selectedTile:
            self.changeColor(COLORS.RED, self.selectedTile)
            if self.selectedTile.getUnit():
                self.UI.displayStats(self.selectedTile.getUnit())
        if self.secondSelectedTile:
            if self.secondSelectedTile.occupiable():
                self.changeColor(COLORS.GREEN, self.secondSelectedTile)
            else:
                self.changeColor(COLORS.RED, self.secondSelectedTile)
        if self.targetedTile:
            self.changeColor(COLORS.YELLOW, self.targetedTile) 
        for row in self.tiles:
            for square in row:
                self.updateImage(square)
                self.drawTile(square.getOutline(), square)

    def resetTiles(self):
        self.window.fill(COLORS.DGREEN)
        for row in self.tiles:
            for square in row:
                self.changeColor(COLORS.BLACK, square)

    def unitOn(self, x, y):
        return self.tileAt(x, y).getUnit()

    def buyUnit(self, x, y, unit):
        testUnit = statreader.unitFromStatsheet('statsheets/'+unit, self.playerActing)
        if self.playerActing.getMoney() >= testUnit.getCost():
            print(self.playerActing)
            self.initializeUnit(x, y, 'statsheets/'+unit, self.playerActing.getTeam())
            self.playerActing.spendMoney(testUnit.getCost())
        else:
            del testUnit

    def getWindow(self):
        return self.window

    def tileFromCoords(self, position):
        x = math.floor(position[0]/self.tileDimensions)
        y = math.floor(position[1]/self.tileDimensions)
        return self.tiles[y][x]

    def updateImage(self, tile):
        if tile.getUnit():
            self.moveImage(tile.getForeground(), tile.getX(), tile.getY())

    def unitProductionFunctionsFrom(self, x, y):
        produceableUnitFunctions = []
        for statsheetName in self.produceableUnits:
            if self.emptySurroundingTiles(x, y) == []:
                produceableUnitFunctions.append((statsheetName[0:-4] + ' No Space', lambda: print(' no space')))
            else:
                produceableUnitFunctions.append((statsheetName[0:-4], lambda statsheetName=statsheetName:self.buyUnit(self.emptySurroundingTiles(x, y)[0].getX(), self.emptySurroundingTiles(x, y)[0].getY(), statsheetName)))
        return produceableUnitFunctions

    def changeColor(self, color, tile):
        tile.changeOutline(color)

    def drawTile(self, color, tile):
        self.changeColor(color, tile)
        pygame.draw.rect(self.window, tile.getOutline(), (tile.getX() * self.tileDimensions, tile.getY() * self.tileDimensions, self.tileDimensions, self.tileDimensions), 1)

    def highlightTile(self, tile, color):
        self.changeColor(color, tile)

    def moveableTilesFrom(self, startTile):
        possibleMoves = self.getReachableSquares(startTile, startTile.getUnit().getSpeed())
        moveOptions = []
        if startTile.getUnit():
            if startTile.getUnit().canMove() and startTile.getUnit().getPlayer() == self.playerActing:
                for move in possibleMoves:
                    square = self.tiles[move[1]][move[0]]
                    if square.occupiable() and not(square == startTile):
                        if self.distanceBetween(startTile, square) <= startTile.getUnit().getSpeed():
                            moveOptions.append(square)
        return moveOptions

    def highlightMoveableTiles(self, startTile):
        if startTile:
            if startTile.getUnit():
                for tile in self.moveableTilesFrom(startTile):
                    self.highlightTile(tile, COLORS.LBLUE)

    def distanceBetween(self, tile1, tile2):
        return abs(tile1.getX() - tile2.getX()) + abs(tile1.getY() - tile2.getY())

    def attackableTilesFrom(self, startTile):
        attackableSquares = []
        if startTile.getUnit():
            if startTile.getUnit().getAttacks() and startTile.getUnit().getPlayer() == self.playerActing:
                for row in self.tiles:
                    for tile in row:
                        if startTile.getUnit() and tile.getUnit():
                            if tile.getUnit().getPlayer() != startTile.getUnit().getPlayer() and self.distanceBetween(startTile, tile) <= startTile.getUnit().getRange():
                                attackableSquares.append(tile)
        return attackableSquares

    def highlightAttackableTiles(self, startTile):
        if startTile:
            if startTile.getUnit():
                for tile in self.attackableTilesFrom(startTile):
                    self.highlightTile(tile, COLORS.RED)

    def attack(self, start, target):
        for square in self.tilesInRange(target, start.getUnit().getRange()):
            if square.getUnit():
                if square.getUnit().getPlayer() != start.getUnit().getPlayer():
                    square.damageUnit(start.getUnit().damageTo(square.getUnit()) * start.getUnit().getDamageFalloff() ** self.distanceBetween(target, square))
        start.getUnit().doAttack()

    def tilesInRange(self, startTile, range):
        for row in self.tiles:
            for square in row:
                if self.distanceBetween(startTile, square) <= range:
                    yield square

    def getPlayerActing(self):
        return self.playerActing

    def generateButtons(self):
        self.UI.clearButtons()
        try:
            if self.selectedTile.getUnit().getName() == 'castle' and self.selectedTile.getUnit().getPlayer() == self.playerActing:
                self.UI.generateButtons(*self.unitProductionFunctionsFrom(self.selectedTile.getX(), self.selectedTile.getY()))
        except:
            pass

    def nextTurn(self):
        for row in self.tiles:
            for square in row:
                if square.getUnit():
                    square.getUnit().nextTurn()
        if self.playerActing == self.player0:
            self.playerActing = self.player1
        else:
            self.playerActing = self.player0
        self.doIncome(self.playerActing)

    def unitsOfPlayer(self, player):
        unitList = []
        for y in self.tiles:
            for tile in y:
                if tile.getUnit():
                    if tile.getUnit().getPlayer() == player:
                        unitList.append(tile.getUnit())
        return unitList
    
    def doIncome(self, player):
        income = 0
        for unit in self.unitsOfPlayer(player):
            income += unit.getProduction()
        player.makeIncome(income)
        
    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height

    def moveThroughable(self, tile):
        return tile.moveThroughable(self.playerActing)

    def getReachableSquares(self, start, max_speed):
        rows = len(self.tiles)
        cols = len(self.tiles[0])

        # Directions: up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Initialize BFS queue and visited set
        queue = deque([(start.getX(), start.getY(), 0)])  # (x, y, distance)
        visited = set()
        visited.add(start)

        reachable = []

        while queue:
            x, y, dist = queue.popleft()

            # If the unit's distance is within the max_speed, add it to reachable list
            if dist <= max_speed:
                reachable.append((x, y))

            # If distance exceeds max_speed, no need to explore further from here
            if dist >= max_speed:
                continue

            # Explore all 4 possible directions
            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                # Check if new position is within bounds and not an obstacle
                if 0 <= nx < cols and 0 <= ny < rows and self.moveThroughable(self.tiles[ny][nx]):
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny, dist + 1))

        return reachable

    def surroundingTiles(self, x, y):
        directions = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        surroundingTiles = []
        for direction in directions:
            try:
                if y + direction[1] >= 0:
                    surroundingTiles.append(self.tileAt(x + direction[0], y + direction[1]))
            except:
                pass
        return surroundingTiles

    def emptySurroundingTiles(self, x, y):
        emptyTiles = []
        for tile in self.surroundingTiles(x, y):
            if tile.occupiable():
                emptyTiles.append(tile)
        return emptyTiles

    def getPlayerNum(self, num):
        if num:
            return self.player1
        else:
            return self.player0