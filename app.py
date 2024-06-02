import requests
import settings
from tildagonos import tildagonos
from app import App
from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES
from system.eventbus import eventbus
from system.patterndisplay.events import *

ERROR_FILE_LOCATION = "/apps/hab-flash/error.log"
URL = "http://151.216.211.144:8000/api/print"
LINE_HEIGHT = 22
OFFSET = -26
LOCATIONS = [
    "Robot Arms",
    "Null Sector",
    "Stage B",
    "Food",
    "Workshop 4",
    "Toilet(?)",
    "Stage A",
    "Stage C",
]

MAX_LED = 12
MIN_LED = 1

class SpinningLight:
    def __init__(self, start = MIN_LED, color = (255, 255, 255), max_delay = 1, delta = 1):
        self.color = color
        self.max_delay = max_delay
        self.delta = delta
        
        self.current_led = start
        self.delay = self.max_delay

    def update(self):
        self.delay -= 1
        if self.delay <= 0: 
            self.current_led += self.delta
            self.delay = self.max_delay

        if self.current_led > MAX_LED: self.current_led = MIN_LED
        elif self.current_led < MIN_LED: self.current_led = MAX_LED 

class HabFlash(App):
    def __init__(self):
        super().__init__()
        self.button_states = Buttons(self)
        self.error = None
        self.name = settings.get("name")
        self.location_index = 0
        self.message_delay = 0
        self.message = None
        self.trails = [
            SpinningLight(start=MIN_LED, color=(0, 0, 255), max_delay = 2, delta = 1),
            SpinningLight(start=4, color=(0, 255, 0), max_delay = 1, delta = -1),
            SpinningLight(start=10, color=(0, 255, 255), max_delay = 2, delta = -1),
            SpinningLight(start=8, color=(255, 0, 0), max_delay = 2, delta = 1),
            SpinningLight(start=8, color=(255, 255, 0), max_delay = 1, delta = -1),
            SpinningLight(start=6, color=(255, 0, 255), max_delay = 1, delta = 1),
        ]

        eventbus.emit(PatternDisable())
    
    def update(self, delta):
        try:
            # user input
            if self.button_states.get(BUTTON_TYPES["CANCEL"]):
                for i in range(MIN_LED, MAX_LED+1): tildagonos.leds[i] = (0, 0, 0) # clear all LEDS
                self.button_states.clear()
                self.minimise()
                return

            elif self.button_states.get(BUTTON_TYPES["UP"]): 
                self.location_index -= 1
                if self.location_index < 0: self.location_index = len(LOCATIONS) - 1
            elif self.button_states.get(BUTTON_TYPES["DOWN"]):
                self.location_index += 1
                if self.location_index >= len(LOCATIONS): self.location_index = 0
            elif self.button_states.get(BUTTON_TYPES["CONFIRM"]):
                self._send_location(LOCATIONS[self.location_index])
            self.button_states.clear()

            # display message
            if self.message_delay > 0: self.message_delay -= 1
            else: self.message = None

            # flash stuff
            for trail in self.trails: 
                trail.update()

            for i in range(MIN_LED, MAX_LED+1): tildagonos.leds[i] = (0, 0, 0)
            for trail in self.trails: 
                tildagonos.leds[trail.current_led] = trail.color
            tildagonos.leds.write()
        except Exception as e:
            self.message = str(e)
            self.delay = 20

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
        try:
            clear_background(ctx)
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.move_to(0, OFFSET).gray(1).text("! HAB FLASH !")
            ctx.move_to(0, OFFSET + LINE_HEIGHT).gray(1).text("I'm at")
            ctx.move_to(0, OFFSET + 2*LINE_HEIGHT).gray(1).text(LOCATIONS[self.location_index])
            
            if self.message is not None:
                for i, line in enumerate(self.message.split("\n")):
                    ctx.move_to(0, OFFSET + (3 + i) * LINE_HEIGHT).rgb(1,0,0).text(str(line))
        except Exception as e:
            self.message = str(e)
            self.delay = 20

    def _exit(self):
        self._reset()
        self.button_states.clear()

__app_export__ = HabFlash
