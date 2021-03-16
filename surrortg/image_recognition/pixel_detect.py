import sys

import cv2

CLOSE = 25


def get_pixel_detector(pixels, close=CLOSE):
    """Get a detector function for spesific pixels

    :param pixels: list of pixels as ((x, y), (r, g, b))
    :type pixels: [(tuple,tuple)]
    :param close: how close rgb value is a match, defaults to 25
    :type close: int, optional
    """

    def _is_close(frame, x, y, r, g, b):
        bgr = frame[y][x]
        return (
            abs(bgr[0] - b) < CLOSE
            and abs(bgr[1] - g) < CLOSE
            and abs(bgr[2] - r) < CLOSE
        )

    def _detector(frame):
        for (x, y), (r, g, b) in pixels:
            if not _is_close(frame, x, y, r, g, b):
                return False
        return True

    return _detector


def main(frame, name):
    """Print example code for 'get_pixel_detector' function

    Usage: python pixel_detect.py <path_to_frame> <detectable_name>
    """

    def _on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(
                f"    (({x}, {y}), ("
                f"{frame[y][x][2]}, {frame[y][x][1]}, {frame[y][x][0]})),"
            )
            cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)
            cv2.imshow("pixel_value_debug", frame)

    cv2.namedWindow("pixel_value_debug", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("pixel_value_debug", _on_mouse)
    cv2.imshow("pixel_value_debug", frame)
    print("# ((x, y), (r, g, b))")
    print(f"{name}_PIXELS = [")
    cv2.waitKey(0)
    print("]\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python pixel_detect.py <path_to_frame> <detectable_name>"
        )
        sys.exit(0)

    print(
        """
Click the pixels to detect, example script is printed during the usage
press Q to exit

Printed values can be used together with 'get_pixel_detector'-function
For example:


import asyncio
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector
    """
    )

    name = sys.argv[2]
    name_lower = name.lower()
    name_upper = name.upper()
    main(cv2.imread(sys.argv[1]), name_upper)

    print(
        f"""
SOURCE = "/dev/video21"

async def main():
    # create {name_lower} detector
    has_{name_lower} = get_pixel_detector({name_upper}_PIXELS)

    # create capture device
    async with await AsyncVideoCapture.create(SOURCE) as frames:
        async for frame in frames:
            # print if {name_lower} is detected
            if has_{name_lower}(frame):
                print("has {name_lower}")
            else:
                print("doesn't have {name_lower}")

asyncio.run(main())
    """
    )
