import unit
import pygame
import os
import player

def getList(fileName):
    file = open(fileName, 'r').read()
    return file.split('\n')

def unitFromStatsheet(statsheet, player, dimensions=20, prebuilt=False):
    statList = getList(statsheet)
    bonuses = statList[9].split('=')[1].split(',')
    bonuses = [tuple(bonus.split(':')) for bonus in bonuses]
    bonusesList = []
    for bonus in bonuses:
        exceptions = bonus[0].split('!')[1].split('|') if '!' in bonus[0] else []
        bonusesList.append(unit.Bonus(
            tags=bonus[0].split('!')[0].split('|'),
            multiplier=float(bonus[1]),
            exceptions=exceptions
        ))

    # Handle status_on_hit parameter (optional, may not exist in older statsheets)
    status_on_hit = None
    if len(statList) > 15:  # Check if status_on_hit field exists
        status_line = statList[15].split('=')
        if len(status_line) > 1 and status_line[1].strip():
            status_on_hit = status_line[1].strip()

    return unit.Unit(
        name=statList[0].split('=')[1],
        attack=int(statList[1].split('=')[1]),
        hp=int(statList[2].split('=')[1]),
        armor=int(statList[3].split('=')[1]),
        speed=int(statList[4].split('=')[1]),
        range=int(statList[5].split('=')[1]),
        cost=int(statList[6].split('=')[1]),
        area=int(statList[7].split('=')[1]),
        damageFalloff=float(statList[8].split('=')[1]),
        bonuses=unit.Bonuses(*bonusesList),
        tags=statList[10].split('=')[1].split(','),
        image=pygame.transform.scale(imageColorConverter('statsheets/images/' + statList[11].split('=')[1], player), (dimensions,dimensions)),
        player=player,
        attacks=int(statList[12].split('=')[1]),
        production=int(statList[13].split('=')[1]),
        hotkey=(statList[14].split('=')[1]),
        inProgress=not(prebuilt),
        status_on_hit=status_on_hit
    )

def imageColorConverter(image, player):
    image = pygame.image.load(image)

    width, height = 40, 40
    if player:
        if player.getTeam():
            colorSet = (255, 0, 0)
        else:
            colorSet = (0, 100, 255)
    
        for x in range(width):
            for y in range(height):
                color = image.get_at((x, y))
                if color == (255, 0, 255, 255):
                    image.set_at((x, y), colorSet)
    
    return image

# Rest of your existing statreader code remains the same...
testUnits = []
for statsheetName in os.listdir('statsheets'):
    if statsheetName != 'images':
        testUnits.append(unitFromStatsheet('statsheets/' + statsheetName, None))

def units_without_tag(tag):
    unitsWithoutTag = []
    for testUnit in testUnits:
        if not(tag in testUnit.getTags()):
            unitsWithoutTag.append(testUnit.getStatsheetName())
    return unitsWithoutTag

def units_with_tag(tag):
    unitsWithTag = []
    for testUnit in testUnits:
        if tag in testUnit.getTags():
            unitsWithTag.append(testUnit.getStatsheetName())
    return unitsWithTag

def cost_of(statsheet):
    statList = getList('statsheets/' + statsheet)
    return int(statList[6].split('=')[1])

def hotkey_of(statsheet):
    statList = getList('statsheets/' + statsheet)
    return statList[14].split('=')[1]