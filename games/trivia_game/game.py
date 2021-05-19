import asyncio
import logging
import time

from games.trivia_game.config import (
    AMOUNT_OF_PLAYERS,
    CORRECT_ROW,
    FIRST_SERVO_PIN,
    SERVO_MIN_PULSE_WIDTH,
    SERVO_MAX_PULSE_WIDTH,
    SERVO_MIN_FULL_SWEEP_TIME,
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
        if self.option == "a":
            return 0.4
        elif self.option == "b":
            return 0
        else:
            return -0.4

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

    def set_all_seats_to(self, b):
        for k in self.seat_input_enabled:
            self.seat_input_enabled[k] = b
     
    def set_seat_to(self, seat, b):
        self.seat_input_enabled[seat] = b

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
        # Initialize servos
        for i in range(0, AMOUNT_OF_PLAYERS):
            servo = Servo(
                FIRST_SERVO_PIN+i,
                SERVO_MIN_PULSE_WIDTH,
                SERVO_MAX_PULSE_WIDTH,
                SERVO_MIN_FULL_SWEEP_TIME,
                SERVO_ROTATION_UPDATE_FREQ,
            )
            self.servos.append(servo)
            await servo.rotate_to(0)
        
        # Add switches for options a, b and c
        for option in ["a", "b", "c"]:
            servo_switch = ServoSwitch(self.servos, option, self.switch_callback)
            self.inputs.append(servo_switch)
            # Register input
            # You can bind this input to a key or mobile button
            # from the admin panel.
            self.io.register_inputs({option: servo_switch})

    async def on_pre_game(self):
        # Set points to 0 for everyone
        self.points = [0] * AMOUNT_OF_PLAYERS
        self.answer_n = 0

    async def on_start(self):
        logging.info("Game started")
        self.log_player_seats()
        await self.question_loop()

    async def on_finish(self):
        # Disable controls
        self.io.disable_inputs()
    
    async def question_loop(self):
        while self.answer_n < len(CORRECT_ROW):
            await self.ask_question()
            self.answer_n += 1
        logging.info("Ending Game")
        self.update_points(True)

    async def ask_question(self):
        self.answers = []
        await self.count_down(20, f"Movint servos to start position {self.question_number()} in")
        await self.set_all_servos(1)
        await self.count_down(10, f"starting the question {self.question_number()} in")
        start_of_question = time.time()
        self.set_all_inputs(True)
        await self.count_down(20, f"closing the question {self.question_number()} in")
        self.set_all_inputs(False)
        correct_count = 0
        logging.info(f"Correct answers is {CORRECT_ROW[self.answer_n]}")
        for answer in self.answers:
            seat = answer["seat"]
            answer_time = answer["time"] - start_of_question
            if answer["correct"]:
                points_by_position = max(4-correct_count, 1)
                correct_count += 1
                logging.info(f"Correct answer {self.player_username(seat)} - " + 
                f"{points_by_position} - {answer_time}")
                self.points[seat] += points_by_position
            else:
                logging.info(f"Wrong answer {self.player_username(seat)} - {answer_time}")
        logging.info(f"Correct answers {correct_count}/{AMOUNT_OF_PLAYERS}")
        self.update_points()

    async def count_down(self, to, message):
        current = to
        while current > 0:
            logging.info(f"{message} {current}/{to}")
            await asyncio.sleep(1)
            current -= 1
        logging.info(f"{message} done")
    
    def update_points(self, is_final = False):
        self.io.send_score(scores=self.points, final_score=is_final)
    
    def is_correct_answer(self, option):
        return CORRECT_ROW[self.answer_n] == option
    
    def set_all_inputs(self, to):
        for i in self.inputs:
            i.set_all_seats_to(to)
    
    def player_username(self, seat):
        try:
            for p in self.players:
                if p["seat"] == seat:
                    return p["username"]
        except:
            return "unknown"
    
    def log_player_seats(self):
        try:
            for p in self.players:
                seat = p["seat"]
                username = p["username"]
                logging.info(f"seat {seat}: {username}")
        except:
            logging.info(f"error while printing seats")
    
    def question_number(self):
        return self.answer_n + 1
    
    async def set_all_servos(self, to):
        for s in self.servos:
            logging.info(f"set_all_servos to {to} currently at {s._pin}")
            await s.rotate_to(to)

    def switch_callback(self, seat, option):
        for i in self.inputs:
            i.set_seat_to(seat, False)
        
        self.answers.append({
            "time": time.time(),
            "option": option,
            "seat": seat,
            "correct": self.is_correct_answer(option)
        })
        logging.info(f"Player {seat} answers {option}")

if __name__ == "__main__":
    # Start running the game
    TriviaGame().run()