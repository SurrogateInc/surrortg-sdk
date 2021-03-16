"""
ocr.py is used to read the times from the score screen

'get_time_ms' gets a frame and the detected position as input, and outputs the
time in milliseconds and as a string.

The numbers are read based on the detected lines (digital style numbers):

  0
  _
1| |2
 |_|
 |3|
4|_|5
  6
"""

# mapping from 'detected line numbers' to 'number'
NUMBERS = {
    (0, 1, 2, 4, 5, 6): 0,
    (2, 5): 1,
    (0, 2, 3, 4, 6): 2,
    (0, 2, 3, 5, 6): 3,
    (1, 2, 3, 5): 4,
    (0, 1, 3, 5, 6): 5,
    (0, 1, 3, 4, 5, 6): 6,
    (0, 2, 5): 7,
    (0, 1, 2, 3, 4, 5, 6): 8,
    (0, 1, 2, 3, 5, 6): 9,
}


# offset from the left top corner to line position
# pixels which are read
NUM_LINES_FROM_CORNER = {
    0: [[9, 2]],
    1: [[2, 8]],
    2: [[17, 8], [9, 9]],
    3: [[9, 15]],
    4: [[1, 23]],
    5: [[17, 22], [9, 22]],
    6: [[9, 28]],
}

# y-values for positions 1-4
# tells the row where the number left corners are
POSITION_YS = {
    1: 31,
    2: 103,
    3: 173,
    4: 245,
}

# number corner x-values
NUMBER_XS = [1094, 1131, 1156, 1193, 1219, 1245]
TENS_OF_MINS_X = 1060  # this only exists if the time is +10 min

# how close match is required when deciding is a pixel line or not
# 0-255, 0 means perfect match
CLOSE = 100

# line color in rgb
LINE_COL = (5, 32, 51)


def _is_line(frame, x, y):
    """Returns True/False based on is the xy pixel on frame line or not

    :return: Is xy pixel line or not
    :rtype: bool
    """

    bgr = frame[y][x]
    return (
        abs(bgr[0] - LINE_COL[2]) < CLOSE
        and abs(bgr[1] - LINE_COL[1]) < CLOSE
        and abs(bgr[2] - LINE_COL[0]) < CLOSE
    )


def _get_num(frame, top_left_corner):
    """Detect 0-9 (or None) from the frame top_left_corner location

    :return: Number 0 to 9 or None
    :rtype: int/None
    """

    result = []
    for num, coords_list in NUM_LINES_FROM_CORNER.items():
        for x, y in coords_list:
            if _is_line(frame, top_left_corner[0] + x, top_left_corner[1] + y):
                result.append(num)
                break
    try:
        return NUMBERS[tuple(result)]
    except KeyError:
        return None


def get_time_ms(frame, position):
    """Get time in ms and string based on the finishing position

    :param frame: A frame from AsyncVideoCapture / cv2.VideoCapture
    :type frame: numpy.ndarray
    :param position: Position 1-4
    :type position: int
    :return: Time in milliseconds, time as string
    :rtype: (int, string)
    """

    y = POSITION_YS[position]
    nums = [_get_num(frame, [x, y]) for x in NUMBER_XS]
    tens_of_mins = _get_num(frame, [TENS_OF_MINS_X, y])
    if isinstance(tens_of_mins, int) and isinstance(nums[0], int):
        nums[0] = 10 * tens_of_mins + nums[0]
    time_string = f"{nums[0]}:{nums[1]}{nums[2]}.{nums[3]}{nums[4]}{nums[5]}"
    if None in nums:
        return None, time_string
    time_ms = int(
        (
            float(f"{nums[1]}{nums[2]}.{nums[3]}{nums[4]}{nums[5]}")
            + 60 * nums[0]
        )
        * 1000
    )
    return time_ms, time_string


if __name__ == "__main__":  # noqa:C901
    import sys

    if len(sys.argv) != 2:
        print(
            """
Runs 3 tests to check that the detections are consistent
Usage: python -m games.ninswitch.ocr <path_to_saved_frames>

The successful frames should be named like this:
2-35-679_1_1604693129851.jpg (time_position_timestamp),
and the failed frames should start with 'FAILED_' prefix.
This is the default naming when SAVE_POS_FRAMES is used

The tests make sure that
    1. previously successful frames still output the same time
    2. previously failed frames still fail
    3. shows one digit on each position for manual checking
            """
        )
        sys.exit(0)

    import pathlib

    import cv2

    from games.ninswitch.game_irlkart import (
        POS_1_PIXELS,
        POS_2_PIXELS,
        POS_3_PIXELS,
        POS_4_PIXELS,
    )
    from surrortg.image_recognition import get_pixel_detector

    position_detectors = {
        1: get_pixel_detector(POS_1_PIXELS),
        2: get_pixel_detector(POS_2_PIXELS),
        3: get_pixel_detector(POS_3_PIXELS),
        4: get_pixel_detector(POS_4_PIXELS),
    }

    def get_position(frame):
        detected = None
        for position in position_detectors.keys():
            if position_detectors[position](frame):
                detected = position
                break
        return detected

    path = sys.argv[1]

    def succesfull_frames():
        for f in pathlib.Path(path).iterdir():
            if not f.is_file():
                continue
            if not f.name.startswith("FAILED_"):
                yield cv2.imread(str(f.absolute())), f.name

    def failed_frames():
        for f in pathlib.Path(path).iterdir():
            if not f.is_file():
                continue
            if f.name.startswith("FAILED_"):
                yield cv2.imread(str(f.absolute())), f.name

    def check_successfull():
        i = 0
        for i, (frame, name) in enumerate(succesfull_frames()):
            try:
                prev_pos = int(name[-19])
                position = get_position(frame)
                if prev_pos != position:
                    print(
                        f"Different position found for {name}, "
                        f"was {prev_pos} is now {position})"
                    )
                else:
                    time_ms, time_string = get_time_ms(frame, prev_pos)
                    cleaned_time = time_string.replace(":", "-").replace(
                        ".", "-"
                    )
                    time = f"{cleaned_time}_{prev_pos}"
                    if time_ms is None:
                        print(f"Time not found for {name}")
                    elif time != name[0:10]:
                        print(
                            f"Different time found for {name}, "
                            f"was {name[0:10]} is now {time}"
                        )
            except Exception as e:
                print(f"Error for {name}: {e}")
        print(f"{i} successful checked")

    def check_failed():
        i = 0
        for i, (frame, name) in enumerate(failed_frames()):
            try:
                # try get position
                position = get_position(frame)
                # if found, check can find time
                if position is not None:
                    print(f"pos {position} found for failed {name})")
                    time_ms, time_string = get_time_ms(frame, position)
                    if time_ms is not None:
                        print(f"time {time_string} found for failed {name})")
            except Exception as e:
                print(f"Error for {name}: {e}")
        print(f"{i} failed checked")

    def show_one(pos, index, value):
        print(
            f"Finding pos: {pos}, index: {index}, value: {value}... ",
            end="",
            flush=True,
        )
        for frame, name in succesfull_frames():
            position = int(name[-19])
            if position == pos and name[index] == value:
                print("\t\tFound!. Press any key to continue.")
                cv2.imshow("frame", frame)
                cv2.waitKey(0)
                return True
        print("\t\tNot found")
        return False

    def show_one_each():
        total = 0
        found = 0
        for pos in [1, 2, 3, 4]:
            for index in [0, 2, 3, 5, 6, 7]:
                for value in range(10):
                    if index == 2 and value > 5:
                        continue  # seconds cannot be >= 60
                    total += 1
                    if show_one(pos, index, str(value)):
                        found += 1
        print(f"{found}/{total} showed")

    print(f"Using frames from: {path} for tests:")
    print("\n1. Checking that previously successful frames still succeed")
    check_successfull()
    print("\n2. Checking that previously failed frames still fail")
    check_failed()
    print("\n3. Showing one of each digit on each position")
    show_one_each()
    print("\nTests finished")
