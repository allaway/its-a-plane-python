import time
import sys
import os

from animator import Animator
from overhead import Overhead

from rgbmatrix import graphics
from rgbmatrix import RGBMatrix, RGBMatrixOptions


# Loop setup
FRAME_RATE = 0.1
FRAME_PERIOD = 1 / FRAME_RATE

# Fonts
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
font_extrasmall = graphics.Font()
font_small = graphics.Font()
font_regular = graphics.Font()
font_large = graphics.Font()
font_extrasmall.LoadFont(f"{DIR_PATH}/fonts/4x6.bdf")
font_small.LoadFont(f"{DIR_PATH}/fonts/5x8.bdf")
font_regular.LoadFont(f"{DIR_PATH}/fonts/6x12.bdf")
font_large.LoadFont(f"{DIR_PATH}/fonts/8x13.bdf")

# Colour helpers
COLOUR_BLACK = graphics.Color(0, 0, 0)
COLOUR_WHITE = graphics.Color(255, 255, 255)
COLOUR_YELLOW = graphics.Color(255, 255, 0)
COLOUR_BLUE = graphics.Color(55, 14, 237)
COLOUR_BLUE_LIGHT = graphics.Color(153, 204, 255)
COLOUR_PINK = graphics.Color(200, 0, 200)
COLOUR_GREEN = graphics.Color(0, 200, 0)
COLOUR_ORANGE = graphics.Color(227, 110, 0)

# Element colours
FLIGHT_NUMBER_COLOUR = COLOUR_BLUE_LIGHT
DIVIDING_BAR_COLOUR = COLOUR_GREEN
DATA_INDEX_COLOUR = COLOUR_WHITE
JOURNEY_COLOUR = COLOUR_YELLOW
ARROW_COLOUR = COLOUR_ORANGE
PLANE_DETAILS_COLOUR = COLOUR_PINK
BLINKER_COLOUR = COLOUR_WHITE

# Element Positions
ARROW_POINT_POSITION = (35, 7)
ARROW_WIDTH = 5
ARROW_HEIGHT = 10

BAR_STARTING_POSITION = (0, 18)
BAR_PADDING = 2

BLINKER_POSITION = (63, 0)
BLINKER_STEPS = 10

DATA_INDEX_POSITION = (52, 21)
DATA_INDEX_TEXT_HEIGHT = 6

FLIGHT_NO_POSITION = (1, 21)
FLIGHT_NO_TEXT_HEIGHT = 8  # based on font size

JOURNEY_POSITION = (0, 0)
JOURNEY_HEIGHT = 12
JOURNEY_WIDTH = 64

PLANE_DISTANCE_FROM_TOP = 30
PLANE_TEXT_HEIGHT = 9

# Constants
MAX_WIDTH = 64
MAX_HEIGHT = 32
MAX_STATIC_TEXT_LEN = 12


class Display(Animator):
    def __init__(self):
        super().__init__(FRAME_RATE)

        # Setup Display
        options = RGBMatrixOptions()
        options.hardware_mapping = "adafruit-hat-pwm"
        options.rows = 32
        options.cols = 64
        options.chain_length = 1
        options.parallel = 1
        options.row_address_type = 0
        options.multiplexing = 0
        options.pwm_bits = 11
        options.brightness = 100
        options.pwm_lsb_nanoseconds = 130
        options.led_rgb_sequence = "RGB"
        options.pixel_mapper_config = ""
        options.show_refresh_rate = 0
        options.gpio_slowdown = 1
        options.disable_hardware_pulsing = True
        options.drop_privileges = True
        self.matrix = RGBMatrix(options=options)

        # Setup canvas
        self.canvas = self.matrix.CreateFrameCanvas()
        self.canvas.Clear()

        # Element positions
        self.plane_position = MAX_WIDTH

        # Data to render
        self._data_index = 0
        self._data_all_looped = False
        self._data = []

        # Start Looking for planes
        self.overhead = Overhead()
        self.overhead.grab_data()

    def draw_square(self, x0, y0, x1, y1, colour):
        for x in range(x0, x1):
            _ = graphics.DrawLine(self.canvas, x, y0, x, y1, colour)

    @Animator.KeyFrame.add(0)
    def flight_details(self):

        # Guard against no data
        if len(self._data) == 0:
            self.canvas.Clear()
            return

        # Clear the area
        self.draw_square(
            0,
            BAR_STARTING_POSITION[1] - (FLIGHT_NO_TEXT_HEIGHT // 2),
            MAX_WIDTH - 1,
            BAR_STARTING_POSITION[1] + (FLIGHT_NO_TEXT_HEIGHT // 2),
            COLOUR_BLACK,
        )

        # Draw flight number if available
        flight_no_text_length = 0
        if (
            self._data[self._data_index]["callsign"]
            and self._data[self._data_index]["callsign"] != "N/A"
        ):
            flight_no = f'{self._data[self._data_index]["callsign"]}'

            flight_no_text_length = graphics.DrawText(
                self.canvas,
                font_small,
                FLIGHT_NO_POSITION[0],
                FLIGHT_NO_POSITION[1],
                FLIGHT_NUMBER_COLOUR,
                flight_no,
            )

        # Draw bar
        if len(self._data) > 1:
            # Clear are where N of M might have been
            self.draw_square(
                DATA_INDEX_POSITION[0] - BAR_PADDING,
                BAR_STARTING_POSITION[1] - (FLIGHT_NO_TEXT_HEIGHT // 2),
                MAX_WIDTH,
                BAR_STARTING_POSITION[1] + (FLIGHT_NO_TEXT_HEIGHT // 2),
                COLOUR_BLACK,
            )

            # Dividing bar
            graphics.DrawLine(
                self.canvas,
                flight_no_text_length+ BAR_PADDING,
                BAR_STARTING_POSITION[1],
                DATA_INDEX_POSITION[0] - BAR_PADDING,
                BAR_STARTING_POSITION[1],
                DIVIDING_BAR_COLOUR,
            )

            # Draw text
            text_length = graphics.DrawText(
                self.canvas,
                font_extrasmall,
                DATA_INDEX_POSITION[0],
                DATA_INDEX_POSITION[1],
                DATA_INDEX_COLOUR,
                f"{self._data_index + 1}/{len(self._data)}",
            )
        else:
            # Dividing bar
            graphics.DrawLine(
                self.canvas,
                flight_no_text_length + BAR_PADDING if flight_no_text_length else 0,
                BAR_STARTING_POSITION[1],
                MAX_WIDTH,
                BAR_STARTING_POSITION[1],
                COLOUR_BLUE,
            )

    @Animator.KeyFrame.add(0)
    def journey(self):

        # Guard against no data
        if len(self._data) == 0:
            return

        if not (
            self._data[self._data_index]["origin"]
            and self._data[self._data_index]["destination"]
        ):
            return

        journey = f"{self._data[self._data_index]['origin']}  {self._data[self._data_index]['destination']}"

        # Draw background
        self.draw_square(
            JOURNEY_POSITION[0],
            JOURNEY_POSITION[1],
            JOURNEY_POSITION[0] + JOURNEY_WIDTH - 1,
            JOURNEY_POSITION[1] + JOURNEY_HEIGHT - 1,
            COLOUR_BLACK,
        )

        # Draw text
        text_length = graphics.DrawText(
            self.canvas,
            font_large,
            0,
            JOURNEY_HEIGHT,
            JOURNEY_COLOUR,
            journey,
        )

    @Animator.KeyFrame.add(1)
    def plane_details(self, count):

        # Guard against no data
        if len(self._data) == 0:
            return

        plane = f'{self._data[self._data_index]["plane"]}'

        # Draw background
        self.draw_square(
            0,
            PLANE_DISTANCE_FROM_TOP - PLANE_TEXT_HEIGHT,
            MAX_WIDTH,
            MAX_HEIGHT,
            COLOUR_BLACK,
        )

        # Draw text
        text_length = graphics.DrawText(
            self.canvas,
            font_regular,
            self.plane_position,
            PLANE_DISTANCE_FROM_TOP,
            PLANE_DETAILS_COLOUR,
            plane,
        )

        # Handle scrolling
        self.plane_position -= 1
        if self.plane_position + text_length < 0:
            self.plane_position = MAX_WIDTH
            if len(self._data) > 1:
                self._data_index = (self._data_index + 1) % len(self._data)
                self._data_all_looped = (not self._data_index) or self._data_all_looped
                self.reset_scene()

    @Animator.KeyFrame.add(0)
    def journey_arrow(self):
        # Guard against no data
        if len(self._data) == 0:
            return

        if not (
            self._data[self._data_index]["origin"]
            and self._data[self._data_index]["destination"]
        ):
            return

        # Black area before arrow
        self.draw_square(
            ARROW_POINT_POSITION[0] - ARROW_WIDTH,
            ARROW_POINT_POSITION[1] - (ARROW_HEIGHT // 2),
            ARROW_POINT_POSITION[0],
            ARROW_POINT_POSITION[1] + (ARROW_HEIGHT // 2),
            COLOUR_BLACK,
        )
        # Top slash
        graphics.DrawLine(
            self.canvas,
            ARROW_POINT_POSITION[0] - ARROW_WIDTH,
            ARROW_POINT_POSITION[1] - (ARROW_HEIGHT // 2),
            ARROW_POINT_POSITION[0],
            ARROW_POINT_POSITION[1],
            ARROW_COLOUR,
        )
        # Bottom slash
        graphics.DrawLine(
            self.canvas,
            ARROW_POINT_POSITION[0],
            ARROW_POINT_POSITION[1],
            ARROW_POINT_POSITION[0] - ARROW_WIDTH,
            ARROW_POINT_POSITION[1] + (ARROW_HEIGHT // 2),
            ARROW_COLOUR,
        )
        graphics.DrawLine(
            self.canvas,
            ARROW_POINT_POSITION[0] - ARROW_WIDTH,
            ARROW_POINT_POSITION[1] - (ARROW_HEIGHT // 2),
            ARROW_POINT_POSITION[0] - ARROW_WIDTH,
            ARROW_POINT_POSITION[1] + (ARROW_HEIGHT // 2),
            ARROW_COLOUR,
        )

    @Animator.KeyFrame.add(2)
    def loading_pulse(self, count):
        reset_count = False
        if self.overhead.processing:
            brightness = (1 - (count / BLINKER_STEPS)) / 2
            self.canvas.SetPixel(
                BLINKER_POSITION[0],
                BLINKER_POSITION[1],
                brightness * BLINKER_COLOUR.red,
                brightness * BLINKER_COLOUR.green,
                brightness * BLINKER_COLOUR.blue,
            )
            reset_count = (count == BLINKER_STEPS)
        else:
            self.canvas.SetPixel(
                BLINKER_POSITION[0],
                BLINKER_POSITION[1],
                0,
                0,
                0
            )
        return reset_count

    @Animator.KeyFrame.add(FRAME_PERIOD * 5)
    def check_for_loaded_data(self, count):
        if self.overhead.new_data:
            self._data_index = 0
            self._data_all_looped = False
            self._data = self.overhead.data
            self.reset_scene()

    @Animator.KeyFrame.add(1)
    def sync(self, count):
        _ = self.matrix.SwapOnVSync(self.canvas)

    @Animator.KeyFrame.add(FRAME_PERIOD * 20)
    def grab_new_data(self, count):
        if not (self.overhead.processing and self.overhead.new_data) and (
            self._data_all_looped or len(self._data) <= 1
        ):
            self.overhead.grab_data()

    def run(self):
        try:
            # Start loop
            print("Press CTRL-C to stop")
            self.play()

        except KeyboardInterrupt:
            print("Exiting\n")
            sys.exit(0)
