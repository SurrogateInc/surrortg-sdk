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
