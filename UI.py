import pygame
import math
REFERENCE_FONT_SIZE = 20
BASE_SCALE = (600, 800)


class UI(object):
  
    def __init__(self, width, surface, UIstartX, UIstartY, *buttons):
        self.buttons = list(buttons)
        self.width = width
        self.surface = surface
        self.UIstartY = UIstartY
        self.UIstartX = UIstartX
        self.currentButtonList = []
        self.keybinds = []
        self.window_width = BASE_SCALE[0]
        self.window_height = BASE_SCALE[1]
        self.font_size = REFERENCE_FONT_SIZE
        self.x_scaler = 1
        self.y_scaler = 1
        for button in self.buttons:
            button.x += self.width
        self.next_turn_x = buttons[0].x - self.width # Assuming the first button is "next turn"
        self.next_turn_width = buttons[0].width

    def doClick(self, location):
        for button in self.buttons:
            if location[0] >= button.x and location[0] <= button.x+button.width and location[1] >= button.y and location[1] <= button.y+button.height:
                button.eventWhenClick()

    def drawText(self, x, y, write):
        font = pygame.font.Font(None, self.font_size)
        text = font.render(write.encode('utf-8'), True, (0, 0, 0))
        self.surface.blit(text, (x, y))
        # [ord(char) for char in text]
        
    def displayStats(self, unit):
        # Basic stats
        self.drawText(self.UIstartX, self.UIstartY-15, 'Attack:')
        self.drawText(self.UIstartX, self.UIstartY, str(unit.getAttack()))
        self.drawText(self.UIstartX+50, self.UIstartY-15 , 'Health:')
        self.drawText(self.UIstartX+50, self.UIstartY, f'{str(unit.getHp())}/{str(unit.getMaxHp())}')
        self.drawText(self.UIstartX, self.UIstartY+15, 'armor:')
        self.drawText(self.UIstartX, self.UIstartY+30, str(unit.getArmor()))
        self.drawText(self.UIstartX+50, self.UIstartY+15, 'attacks:')
        self.drawText(self.UIstartX+50, self.UIstartY+30, str(unit.getAttacks()))
        self.drawText(self.UIstartX, self.UIstartY+45, unit.getName())
        
        # Construction status
        if unit.is_under_construction():
            self.drawText(self.UIstartX, self.UIstartY+60, f'Under Construction: {unit.get_build_progress()}/{unit.get_build_cost()}')
        
        # Status effects
        status_effects_text = unit.get_status_effects_display()
        if status_effects_text:
            self.drawText(self.UIstartX, self.UIstartY+75, 'Status Effects:')
            # Split long status effect text into multiple lines if needed
            if len(status_effects_text) > 20:
                # Split into chunks of 20 characters
                lines = [status_effects_text[i:i+20] for i in range(0, len(status_effects_text), 20)]
                for i, line in enumerate(lines[:3]):  # Show max 3 lines
                    self.drawText(self.UIstartX, self.UIstartY+90+i*15, line)
            else:
                self.drawText(self.UIstartX, self.UIstartY+90, status_effects_text)
        
        # On-hit status effect info
        if hasattr(unit, 'status_on_hit') and unit.status_on_hit:
            self.drawText(self.UIstartX, self.UIstartY+(135 * self.y_scaler), f'On Hit: {unit.status_on_hit.replace("_", " ").title()}')

    def showPlayerInfo(self, player):
        self.drawText(self.UIstartX+(105 * self.x_scaler), self.UIstartY-(30 * self.y_scaler), 'money:')
        self.drawText(self.UIstartX+(155 * self.x_scaler), self.UIstartY-(30 * self.y_scaler), str(player.getMoney()))
    
    def displayHotkeys(self):
        startY = 500 * self.y_scaler
        for hotkey, function, name in self.keybinds:
            self.drawText(self.UIstartX, startY, f'{hotkey}: {name}')
            startY += (15 * self.y_scaler)
    
    def display_turn_count(self, turnCount):
        self.drawText(self.UIstartX+(105 * self.x_scaler), self.UIstartY-(45 * self.y_scaler), 'turn:')
        self.drawText(self.UIstartX+(155 * self.x_scaler), self.UIstartY-(45 * self.y_scaler), str(math.floor(turnCount)))

    def drawButtons(self):
        for button in self.buttons:
            self.drawButton(button)

    def clearButtons(self):
        for button in self.currentButtonList:
            self.buttons.remove(button)
        self.currentButtonList = []

    def generateButtons(self, *nameFuncsLst):
        start_pos = self.UIstartY + 65
        self.currentButtonList = []
        for name, function in nameFuncsLst:
            self.currentButtonList.append(Button(
                x = self.UIstartX,
                y = start_pos,
                width = 150,
                height = 15,
                label = name,
                eventWhenClick=function
            ))
            self.buttons.append(self.currentButtonList[-1])
            start_pos += 20

    def generateHotkeys(self, *hotkeyFuncsLst):
        self.keybinds = []
        for hotkey, function, name in hotkeyFuncsLst:
            self.keybinds.append((hotkey, function, name))

    def handle_keypress(self, key):
        for hotkey, function, name in self.keybinds:
            if key == hotkey:
                function()

    def drawButton(self, button):
        pygame.draw.rect(self.surface, (0, 128, 255), [button.getX(), button.getY(), button.getWidth(), button.getHeight()])
        self.drawText(button.getX(), button.getY(), button.getLabel())
        
    def set_start(self, x: int, y: int) -> None:
        self.UIstartX = x
        self.UIstartY = y

    def set_board_width(self, width: int) -> None:
        self.window_width = width

    def change_window_width(self, width: int) -> int:
        self.window_width = width
        self.x_scaler = self.window_width / BASE_SCALE[0]
        return int(REFERENCE_FONT_SIZE * self.x_scaler)

    def change_window_height(self, height: int) -> int:
        self.window_height = height
        self.y_scaler = self.window_height / BASE_SCALE[1]
        return int(REFERENCE_FONT_SIZE * self.y_scaler)
    
    def update_dimensions(self, width, height) -> None:
        self.font_size = min(self.change_window_width(width), self.change_window_height(height))

    def change_next_turn_button(self) -> None:
        for button in self.buttons:
            if button.getLabel() == "next turn":
                button.x = int(self.next_turn_x * self.x_scaler) + self.window_width
                button.width = int(self.next_turn_width * self.x_scaler)
                print(button.x, button.width)
  
class Button(object):
  
    def __init__(self, x, y, width, height, label, eventWhenClick):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.eventWhenClick = eventWhenClick

    def getX(self):
        return self.x
    
    def getY(self):
        return self.y
    
    def getLabel(self):
        return self.label
    
    def getWidth(self):
        return self.width
    
    def getHeight(self):
        return self.height