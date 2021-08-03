import logging
from math import sqrt


class ArucoMarker:
    def __init__(self, id, corners, resolution):
        """Class representing an Aruco marker.

        This class is the main way to pass information about detected aruco
        markers. ArucoMarker instances are created in ArucoDetectProcess. New
        markers can be accessed by registering as an observer to ArucoDetect.

        :param id: Aruco marker ID
        :type id: Int
        :param corners: pixel coordinates for the four corners of the marker
        :type corners: Array of array of floats
        :param resolution: Resolution of the video frame in which the marker
            was detected. Used to calculate distance to the marker.
        :type resolution: tuple of two floats
        """
        self.id = id
        self.corners = corners
        self.resolution = resolution

    def __str__(self):
        return (
            f"Aruco marker with id: {self.id}, corners: {self.corners},"
            f"distance: {self.get_distance()}, center location: "
            f"{self.get_location()}, "
            f"from frame with resolution: {self.resolution}"
        )

    def get_distance(self):
        """Calculates "distance" to marker.

        The distance does not represent any real unit, but is calculated
        from the relative size of the marker compared to the size of the
        video frame. Thus, the distance unit depends on the physical size
        of the marker and the physical parameters of the camera. For example,
        a "distance" of 0.05 means that the marker takes up 5% of the camera
        view.

        :return: value between 0 and 1, representing relative size of marker
        :rtype: float
        """
        edge_lengths = [
            sqrt(
                (self.corners[i][0] - self.corners[i - 1][0]) ** 2
                + (self.corners[i][1] - self.corners[i - 1][1]) ** 2
            )
            for i in range(len(self.corners))
        ]
        distance = (max(edge_lengths) ** 2) / (
            self.resolution[0] * self.resolution[1]
        )
        return distance

    # Experimental feature. Requires camera hardware parameters to function.
    def get_real_distance(self, marker_size, sensor_height, focal_length):
        """Calculates physical distance to marker.

        Experimental feature that can measure real distance to marker with
        relatively good accuracy. Requires knowledge of the physical size of
        the aruco marker and hardware parameters of the camera.

        :param marker_size: length of marker in millimeters*100
        :type id: Int
        :param sensor_height: height of sensor in millimeters*100
        :type sensor_height: Int
        :param focal_length: focal length of camera in millimeters*100
        :type focal_length: Int

        :return: distance to marker in millimeters
        :rtype: float
        """
        edge_lengths = [
            sqrt(
                (self.corners[i][0] - self.corners[i - 1][0]) ** 2
                + (self.corners[i][1] - self.corners[i - 1][1]) ** 2
            )
            for i in range(len(self.corners))
        ]
        fix_factor = 8 / 5
        distance = (
            (fix_factor * focal_length * marker_size * self.resolution[1])
            / (max(edge_lengths) * sensor_height)
            / 100
        )
        logging.info(f"real distance: {distance}")
        return distance

    def get_location(self):
        """Calculates location of marker center in pixel coordinates

        :return: center of marker in pixel coordinates
        :rtype: array of two floats
        """
        location = tuple(sum((corner / 4 for corner in self.corners)))
        return location
