import asyncio
import logging
import time

import keyboard

from games.trivia_game.config import (
    AMOUNT_OF_PLAYERS,
    CORRECT_ROW,
    FIRST_SERVO_PIN,
    OPTION_ANGLES,
    RESET_ANGLE,
    SERVO_MAX_PULSE_WIDTH,
    SERVO_MIN_FULL_SWEEP_TIME,
    SERVO_MIN_PULSE_WIDTH,
    SERVO_ROTATION_UPDATE_FREQ,
)
from surrortg import Game
from surrortg.devices import Servo
from surrortg.inputs import Switch


class ServoSwitch(Switch):
    def __init__(self, servos, option, callback):
        self.servos = servos
        self.seat_input_enabled = {}
        for i in range(0, AMOUNT_OF_PLAYERS):
            self.seat_input_enabled[i] = False
        self.option = option
        self.callback = callback

    def servo_rotation(self):
        try:
            return OPTION_ANGLES[self.option]
        except KeyError:
            logging.warning(
                f"Servo angle for option {self.option} not defined"
            )
            return RESET_ANGLE

    async def on(self, seat=0):
        if self.seat_input_enabled[seat]:
            self.callback(seat, self.option)
            logging.info(f"Servo movement for {seat} to {self.option}")
            servo = self.servos[seat]
            rotation = self.servo_rotation()
            logging.info(f"Servo pin {servo._pin} - {rotation}")
            await servo.rotate_to(rotation)
            logging.info(f"Servo movement ended for {seat}")
        else:
            logging.info("Max press count reached")

    async def off(self, seat=0):
        pass

    def set_all_seats_to(self, enabled):
        for seat in self.seat_input_enabled:
            self.seat_input_enabled[seat] = enabled

    def set_seat_to(self, seat, enabled):
        self.seat_input_enabled[seat] = enabled


class TriviaGame(Game):
    """TriviaGame implements the basic game loop.

    It will wait on host keyboard input to start questions
    and enabled/disabled player input for options.
    """

    async def on_init(self):
        self.servos = []
        self.inputs = []
        self.points = []
        self.answers = []
        # The answer the game is currently at
        self.answer_n = 0
        # Boolean to pause the question loop
        self.is_paused = True
        # Keyboard handler for unpausing/pausing the game
        self.pause_hook = keyboard.on_press(self.pause_handler)
        # Initialize servos
        for i in range(0, AMOUNT_OF_PLAYERS):
            servo = Servo(
                FIRST_SERVO_PIN + i,
                SERVO_MIN_PULSE_WIDTH,
                SERVO_MAX_PULSE_WIDTH,
                SERVO_MIN_FULL_SWEEP_TIME,
                SERVO_ROTATION_UPDATE_FREQ,
            )
            self.servos.append(servo)
            await servo.rotate_to(RESET_ANGLE)

        # Check that every answer in 'CORRECT_ROW' has
        # angle set in 'OPTION_ANGLES'
        for answer in CORRECT_ROW:
            if answer not in OPTION_ANGLES:
                raise RuntimeError(
                    f"CORRECT_ROW includes '{answer}' that doesn't have "
                    f"angle set in OPTION_ANGLES"
                )

        # Add switches for all options in OPTION_ANGLES
        for option in OPTION_ANGLES:
            servo_switch = ServoSwitch(
                self.servos, option, self.switch_callback
            )
            self.inputs.append(servo_switch)
            # Register input
            # You can bind this input to a key or mobile button
            # from the admin panel.
            self.io.register_inputs({option: servo_switch})

    async def on_pre_game(self):
        # Set points to 0 for everyone
        self.points = [0] * AMOUNT_OF_PLAYERS
        self.answer_n = 0
        self.is_paused = True

    async def on_start(self):
        logging.info("Game started")
        self.log_player_seats()
        await self.question_loop()

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()

    async def on_exit(self, reason, exception):
        # Unbind pause handler
        try:
            keyboard.unhook(self.pause_hook)
        except (AttributeError, KeyError):
            pass

    async def question_loop(self):
        while self.answer_n < len(CORRECT_ROW):
            await self.ask_question()
            self.answer_n += 1
        logging.info("Ending Game")
        self.update_points(True)

    async def ask_question(self):
        await self.wait_pause()
        self.answers = []
        await self.count_down(
            20,
            f"Moving the servos to start position {self.question_number()} in",
        )
        await self.set_all_servos(RESET_ANGLE)
        await self.count_down(
            10, f"Starting the question {self.question_number()} in"
        )
        start_of_question = time.time()
        self.set_all_inputs(True)
        await self.count_down(
            20, f"Closing the question {self.question_number()} in"
        )
        self.set_all_inputs(False)
        correct_count = 0
        logging.info(f"Correct answers is {CORRECT_ROW[self.answer_n]}")
        for answer in self.answers:
            seat = answer["seat"]
            answer_time = answer["time"] - start_of_question
            if answer["correct"]:
                points_by_position = max(4 - correct_count, 1)
                correct_count += 1
                logging.info(
                    f"Correct answer {self.player_username(seat)} - "
                    f"{points_by_position} - {answer_time}"
                )
                self.points[seat] += points_by_position
            else:
                logging.info(
                    f"Wrong answer {self.player_username(seat)}"
                    f" - {answer_time}"
                )
        logging.info(f"Correct answers {correct_count}/{AMOUNT_OF_PLAYERS}")
        self.update_points()

    async def wait_pause(self):
        while self.is_paused:
            logging.info("Game is paused. Press 1 to continue")
            await asyncio.sleep(1)

    async def count_down(self, to, message):
        current = to
        while current > 0:
            logging.info(f"{message} {current}/{to}")
            await asyncio.sleep(1)
            current -= 1
        logging.info(f"{message} done")

    def update_points(self, is_final=False):
        self.io.send_score(scores=self.points, final_score=is_final)

    def is_correct_answer(self, option):
        return CORRECT_ROW[self.answer_n] == option

    def set_all_inputs(self, to):
        for i in self.inputs:
            i.set_all_seats_to(to)

    def player_username(self, seat):
        # self.players is an array of current players in the game.
        # It includes for e.g. username and queue options of the player.
        for player in self.players:
            if player["seat"] == seat:
                return player["username"]

    def log_player_seats(self):
        for player in self.players:
            seat = player["seat"]
            username = player["username"]
            logging.info(f"seat {seat}: {username}")

    def question_number(self):
        return self.answer_n + 1

    async def set_all_servos(self, to):
        for servo in self.servos:
            logging.info(f"set_all_servos to {to} currently at {servo._pin}")
            await servo.rotate_to(to)

    def switch_callback(self, seat, option):
        for i in self.inputs:
            i.set_seat_to(seat, False)

        self.answers.append(
            {
                "time": time.time(),
                "option": option,
                "seat": seat,
                "correct": self.is_correct_answer(option),
            }
        )
        logging.info(f"Player {self.player_username(seat)} answered {option}")

    def pause_handler(self, key):
        if key.name == "1":
            self.is_paused = False
        elif key.name == "0":
            self.is_paused = True
        else:
            logging.info(
                "Wrong key pressed. Press '1' for unpause and '0' for pause"
            )
            return


if __name__ == "__main__":
    # Start running the game
    TriviaGame().run()
