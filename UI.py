import pygame
import math
from functools import partial
REFERENCE_FONT_SIZE = 20
BASE_SCALE = (400, 800)


class UI(object):
  
    def __init__(self, width, surface, UIstartX, UIstartY, *buttons):
        self.buttons = list(buttons)
        self.width = width
        self.surface = surface
        self.UIstartY = UIstartY
        self.UIstartX = UIstartX
        self.currentButtonList = []
        # Full list of production entries (name, function) when generating many buttons
        self.currentButtonEntries = []
        # Scroll state for production menu
        self.production_scroll_index = 0
        # How many production buttons to show at once
        self.production_view_count = 6
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
        self.next_turn_height = buttons[0].height
        self.next_turn_y = buttons[0].y

    def doClick(self, location):
        # Check regular buttons
        for button in self.buttons:
            if location[0] >= button.x and location[0] <= button.x+button.width and location[1] >= button.y and location[1] <= button.y+button.height:
                button.eventWhenClick()

    def drawText(self, x, y, write):
        font = pygame.font.Font(None, self.font_size)
        text = font.render(write.encode('utf-8'), True, (0, 0, 0))
        self.surface.blit(text, (x, y))
        # [ord(char) for char in text]
    
    def centerText(self, write, width, height):
        font = pygame.font.Font(None, self.font_size)
        textWidth, textHeight = font.size(write)
        y = abs((height-textHeight)/2)
        x = abs((width-textWidth)/2)
        return x, y
    
    def carryButtonEvent(self, tile, item):
        tile.activeUnit = item

    def carryingButtons(self, tile):
        # Remove existing carried unit buttons from main list
        for button in list(self.currentButtonList):
            if button in self.buttons:
                self.buttons.remove(button)
        self.currentButtonList = []
        
        start_pos = 65
        for item in tile.get_unit().carrying:
            is_active = (item == tile.activeUnit)
            buttonFunc = partial(self.carryButtonEvent, tile, item)
            btn = Button(
                x = self.UIstartX,
                y = int(self.y_scaler * (self.UIstartY + start_pos)),
                width = int(150 * self.x_scaler),
                height = int(15 * self.y_scaler),
                label = item.name,
                eventWhenClick=buttonFunc,
                is_highlighted=is_active
            )
            self.currentButtonList.append(btn)
            self.buttons.append(btn)
            start_pos += 20

    def displayStats(self, selectedTile):
        # Basic stats
        unit = selectedTile.get_unit()
        self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY-15), 'Attack:')
        self.drawText(self.UIstartX, self.UIstartY * self.y_scaler, str(unit.getAttack()))
        self.drawText(self.UIstartX+(self.x_scaler * 50), self.y_scaler * (self.UIstartY-15), 'Health:')
        self.drawText(self.UIstartX+(self.x_scaler * 50), self.UIstartY * self.y_scaler, f'{str(unit.getHp())}/{str(unit.getMaxHp())}')
        self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY+15), 'armor:')
        self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY+30), str(unit.getArmor()))
        self.drawText(self.UIstartX+(self.x_scaler * 50), self.y_scaler * (self.UIstartY+15), 'attacks:')
        self.drawText(self.UIstartX+(self.x_scaler * 50), self.y_scaler * (self.UIstartY+30), str(unit.getAttacks()))
        self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY+45), unit.getName())
        if len(unit.carrying) >= 1:
            self.carryingButtons(selectedTile)
            self.drawButtons()
        # Construction status
        if unit.is_under_construction():
            self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY+60), f'Under Construction: {unit.get_build_progress()}/{unit.get_build_cost()}')
        
        # Status effects
        status_effects_text = unit.get_status_effects_display()
        if status_effects_text:
            self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY+75), 'Status Effects:')
            # Split long status effect text into multiple lines if needed
            if len(status_effects_text) > 20:
                # Split into chunks of 20 characters
                lines = [status_effects_text[i:i+20] for i in range(0, len(status_effects_text), 20)]
                for i, line in enumerate(lines[:3]):  # Show max 3 lines
                    self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY(90+i*15)), line)
            else:
                self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY+90), status_effects_text)
        
        # On-hit status effect info
        if hasattr(unit, 'status_on_hit') and unit.status_on_hit:
            self.drawText(self.UIstartX, self.y_scaler * (self.UIstartY+135), f'On Hit: {unit.status_on_hit.replace("_", " ").title()}')

    def showPlayerInfo(self, player):
        self.drawText(self.UIstartX+(105 * self.x_scaler), self.UIstartY * self.y_scaler, 'money:')
        self.drawText(self.UIstartX+(155 * self.x_scaler), self.UIstartY * self.y_scaler, str(player.getMoney()))
    
    def displayHotkeys(self):
        startY = self.y_scaler
        for hotkey, function, name in self.keybinds:
            self.drawText(self.UIstartX, self.window_height - (self.y_scaler * startY), f'{hotkey}: {name}')
            startY += (15)
    
    def display_turn_count(self, turnCount):
        self.drawText(self.UIstartX+(105 * self.x_scaler), (self.UIstartY-45) * self.y_scaler, 'turn:')
        self.drawText(self.UIstartX+(155 * self.x_scaler), (self.UIstartY-45) * self.y_scaler, str(math.floor(turnCount)))

    def drawButtons(self):
        for button in self.buttons:
            self.drawButton(button)

    def clearButtons(self):
        for button in list(self.currentButtonList):
            if button in self.buttons:
                self.buttons.remove(button)
        self.currentButtonList = []
        self.currentButtonEntries = []
        self.production_scroll_index = 0

    def generateButtons(self, *nameFuncsLst):
        # Store the full entries and render a windowed subset with scrolling
        new_entries = list(nameFuncsLst)
        
        # Only reset scroll index if entries changed (different count or transitioning from empty)
        if len(new_entries) != len(self.currentButtonEntries):
            self.production_scroll_index = 0
        
        self.currentButtonEntries = new_entries
        self._refresh_visible_buttons()

    def get_page_info(self):
        """Return page number info as string (e.g., 'Page 1 of 3')"""
        if not self.currentButtonEntries:
            return ""
        current_page = (self.production_scroll_index // self.production_view_count) + 1
        total_pages = (len(self.currentButtonEntries) + self.production_view_count - 1) // self.production_view_count
        return f"Page {current_page} of {total_pages}"

    def _refresh_visible_buttons(self):
        # Remove existing visible buttons
        for button in list(self.currentButtonList):
            if button in self.buttons:
                self.buttons.remove(button)
        self.currentButtonList = []

        start_pos = 65
        
        # Create visible buttons from the current scroll index
        end_index = min(len(self.currentButtonEntries), self.production_scroll_index + self.production_view_count)
        for name, function in self.currentButtonEntries[self.production_scroll_index:end_index]:
            btn = Button(
                x = self.UIstartX,
                y = int(self.y_scaler * (self.UIstartY + start_pos)),
                width = int(150 * self.x_scaler),
                height = int(15 * self.y_scaler),
                label = name,
                eventWhenClick=function,
                is_highlighted=False
            )
            self.currentButtonList.append(btn)
            self.buttons.append(btn)
            start_pos += 20
        
        # Add Previous button if not on first page
        if self.production_scroll_index > 0:
            prev_btn = Button(
                x = self.UIstartX,
                y = int(self.y_scaler * (self.UIstartY + start_pos + 5)),
                width = int(70 * self.x_scaler),
                height = int(15 * self.y_scaler),
                label = "< Prev",
                eventWhenClick=self.scroll_up,
                is_highlighted=False
            )
            self.currentButtonList.append(prev_btn)
            self.buttons.append(prev_btn)
        
        # Add Next button if not on last page
        if self.production_scroll_index + self.production_view_count < len(self.currentButtonEntries):
            next_btn = Button(
                x = self.UIstartX + int(80 * self.x_scaler),
                y = int(self.y_scaler * (self.UIstartY + start_pos + 5)),
                width = int(70 * self.x_scaler),
                height = int(15 * self.y_scaler),
                label = "Next >",
                eventWhenClick=self.scroll_down,
                is_highlighted=False
            )
            self.currentButtonList.append(next_btn)
            self.buttons.append(next_btn)

    def generateHotkeys(self, *hotkeyFuncsLst):
        self.keybinds = []
        for hotkey, function, name in hotkeyFuncsLst:
            self.keybinds.append((hotkey, function, name))

    def scroll_up(self):
        if self.production_scroll_index > 0:
            self.production_scroll_index -= self.production_view_count
            self.production_scroll_index = max(0, self.production_scroll_index)
            self._refresh_visible_buttons()

    def scroll_down(self):
        if self.production_scroll_index + self.production_view_count < len(self.currentButtonEntries):
            self.production_scroll_index += self.production_view_count
            self._refresh_visible_buttons()

    def handle_keypress(self, key):
        for hotkey, function, name in self.keybinds:
            if key == hotkey:
                function()

    def drawButton(self, button):
        # Use yellow for highlighted buttons, blue for normal
        button_color = (255, 200, 0) if button.is_highlighted else (0, 128, 255)
        pygame.draw.rect(self.surface, button_color, [button.getX(), button.getY(), button.getWidth(), button.getHeight()])
        x, y = self.centerText(button.getLabel(), button.getWidth(), button.getHeight())
        self.drawText(button.getX() + x, button.getY() + y, button.getLabel())
        
    def set_start(self, x: int, y: int) -> None:
        self.UIstartX = x
        self.UIstartY = y

    def set_board_width(self, width: int) -> None:
        self.window_width = width

    def change_window_width(self, width: int) -> int:
        self.window_width = width
        self.x_scaler = (2/3)*self.window_width / BASE_SCALE[0]
        return int(REFERENCE_FONT_SIZE * self.x_scaler)

    def change_window_height(self, height: int) -> int:
        self.window_height = height
        self.y_scaler = self.window_height / BASE_SCALE[1]
        return int(REFERENCE_FONT_SIZE * self.y_scaler)
    
    def update_dimensions(self, width, height) -> None:
        self.font_size = min(self.change_window_width(width), self.change_window_height(height))
        self.change_next_turn_button()

    def change_next_turn_button(self) -> None:
        for button in self.buttons:
            if button.getLabel() == "next turn":
                button.x = int(self.next_turn_x * self.x_scaler) + self.UIstartX
                button.y = int(self.next_turn_y * self.y_scaler)
                button.width = int(self.next_turn_width * self.x_scaler)
                button.height = int(self.next_turn_height * self.y_scaler)
                print(button.x, button.width)
  
class Button(object):
  
    def __init__(self, x, y, width, height, label, eventWhenClick, is_highlighted=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.eventWhenClick = eventWhenClick
        self.is_highlighted = is_highlighted

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