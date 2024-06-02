import requests
import settings
from tildagonos import tildagonos
from app import App
from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES

URL = "http://151.216.211.144:8000/api/print"
LINE_HEIGHT = 22
OFFSET = -26

class HabFlash(App):
    def __init__(self):
        super().__init__()
        self.button_states = Buttons(self)
        self.error = None
        self.name = settings.get("name")
        self.locations = [
            "Robot Arms",
            "Null Sector",
            "Stage B",
            "Food",
            "Workshop 4",
            "Toilet(?)",
            "Stage A",
            "Stage C",
            ]
        self.location_index = 0
        self.message_delay = 0
        self.message = None
        self.current_led = 0
    
    def update(self, delta):
        # user input
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            for i in range(0, 13): tildagonos.leds[i] = (0, 0, 0) # clear all LEDS
            self.button_states.clear()
            self.minimise()

        elif self.button_states.get(BUTTON_TYPES["UP"]): 
            self.location_index -= 1
            if self.location_index < 0: self.location_index = len(self.locations) - 1
        elif self.button_states.get(BUTTON_TYPES["DOWN"]):
            self.location_index += 1
            if self.location_index >= len(self.locations): self.location_index = 0
        elif self.button_states.get(BUTTON_TYPES["CONFIRM"]):
            self._send_location(self.locations[self.location_index])

        # display message
        if self.message_delay > 0: self.message_delay -= 1
        else: self.message = None

        # flash stuff
        for i in range(0, 13):
            if self.current_led == i: tildagonos.leds[i] = (255, 255, 255)
            else: tildagonos.leds[i] = (0, 0, 0)
        self.current_led += 1
        if self.current_led > 12: self.current_led = 1
        tildagonos.leds.write()

    def _send_location(self, location):
        try:
            self.error = None
            data = {
                "styles" : [{
                    "double_height": False,
                    "double_width": False,
                    "bold": False,
                    "align": "left",
                    "underline": True
                    },{
                    "double_height": True,
                    "double_width": True,
                    "bold": True,
                    "align": "center",
                    "underline": True
                    },{
                    "double_height": False,
                    "double_width": False,
                    "bold": True,
                    "align": "center",
                    "underline": False
                }],
                "commands" : [
                    { "type": "text", "content": f"LOCATION UPDATE!", "style": 1},
                    { "type": "text", "content": f"--------------", "style": 2},
                    { "type": "text", "content": f"{self.name} is at {location}", "style": 0},
                    { "type": "text", "content": f"--------------", "style": 2}
                ]
            }
            requests.post(URL, json=data)
            self.message = "Location\nUploaded!"
            self.message_delay = 20
        except Exception as e:
            self.message = str(e)

    def draw(self, ctx):
        clear_background(ctx)
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.move_to(0, OFFSET).gray(1).text("! HAB FLASH !")
        ctx.move_to(0, OFFSET + LINE_HEIGHT).gray(1).text("I'm at")
        ctx.move_to(0, OFFSET + 2*LINE_HEIGHT).gray(1).text(self.locations[self.location_index])
        
        if self.message is not None:
            for i, line in enumerate(self.message.split("\n")):
                ctx.move_to(0, OFFSET + (3 + i) * LINE_HEIGHT).rgb(1,0,0).text(str(line))

    def _exit(self):
        self._reset()
        self.button_states.clear()

__app_export__ = HabFlash
