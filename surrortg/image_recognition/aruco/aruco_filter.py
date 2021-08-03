import logging
import time


class ArucoFilter:
    """Helper class for filtering detected Aruco markers.

    Use this helper class to receive callbacks only for aruco markers that
    fulfill the filter criteria. Built-in filters exist for ID, distance,
    and time interval. This class can be useful if you use aruco markers
    for several types of game logic, or just to skip writing boilerplate
    code.

    Extra filters can also be added via the add_filter method.

    Short example of how to integrate the class into game logic:

    .. code-block:: python

        from surrortg.image_recognition.aruco import ArucoFilter

        YourGame(Game):
        async def on_init(self):
            self.aruco_source = await ArucoDetector.create()
            self.filter = ArucoFilter(self.score_logic, self.aruco_source,
                [0,1,2,3,4], 0, 2)

        async def on_start(self):
            self.filter.start()

        def score_logic(self, marker):
            # implement logic for marker that passed filter
            # if final_score:
            #     self.filter.stop()

    :param callback: Function to call if marker passes filters
    :type callback: Function with one ArucoMarker as the only parameter
    :param aruco_source: An ArucoDetector which the filter subscribes to
        in order to receive detected aruco markers
    :type aruco_source: ArucoDetector
    :param ids: Aruco marker IDs which the filter will accept. If this is
        an empty list, all IDs will be accepted. Defaults to an empty list.
    :type ids: list of ints, optional
    :param detect_distance: Distance threshold for accepting an aruco
        marker. Must be between 0 and 1, as the distance is really the
        relative size of the marker in the video frame. If zero, markers
        at any distance are accepted. By default any distance is accepted.
    :type detect_distance: float between 0 and 1, optional
    :param detection_cooldown: If set above zero, a marker can only be
        detected once within the specified cooldown time. Defaults to zero.
    :type detection_cooldown: number, optional
    """

    def __init__(
        self,
        callback,
        aruco_source,
        ids=[],
        detect_distance=0,
        detection_cooldown=0,
    ):
        self.callback = callback
        self.ids = ids
        self.min_dist = detect_distance
        self.aruco_source = aruco_source
        self.det_cd = detection_cooldown
        self.det_times = {}
        self.running = False
        self.filters = [self._filter_by_id, self._filter_by_distance]
        if detection_cooldown > 0:
            self.filters.append(self._filter_by_time)

    def add_filter(self, filter_fun):
        """Add custom filter to the ArucoFilter instance.

        :param filter_fun: Custom filter function
        :type filter_fun: Function with one ArucoMarker as the only parameter
            and truthy return value (i.e. bool)
        """
        self.filters.append(filter_fun)

    def remove_filter(self, filter_fun):
        """Remove custom filter from the ArucoFilter instance.

        :param filter_fun: Custom filter function
        :type filter_fun: Function with one ArucoMarker as the only parameter
            and truthy return value (i.e. bool)
        """
        try:
            self.filters.remove(filter_fun)
        except ValueError as e:
            logging.warning(
                f"error in removing filter from aruco filters: {e}"
            )
            pass

    def start(self):
        """Make the ArucoFilter subscribe for new aruco marker detections.
        Markers which pass the filter will then be sent via the callback
        given at __init__.
        """
        if not self.running:
            self.aruco_source.register_observer(self._detect_cb)
            self.running = True

    def stop(self):
        """Make the ArucoFilter unsubscribe from new aruco marker detections.
        No more markers will be sent via the callback, unless start() is
        called again.
        """
        if self.running:
            self.aruco_source.unregister_observer(self._detect_cb)
            self.running = False

    def set_cooldown(self, cooldown):
        """Set cooldown timer for marker detection.

        :param cooldown: Cooldown time. If zero, no cooldown is used. Otherwise
             a marker will only be detected once every cooldown period.
        :type cooldown: nonnegative number
        """
        if cooldown == 0:
            self.remove_filter(self._filter_by_time)
            self.det_cd = cooldown
            return
        if self.det_cd == 0:
            self.filters.append(self._filter_by_time)
        self.det_cd = cooldown

    def _detect_cb(self, found_markers):
        for marker in found_markers:
            if self._passes_filters(marker):
                self.callback(marker)

    def _filter_by_id(self, marker):
        return len(self.ids) == 0 or marker.id in self.ids

    def _filter_by_distance(self, marker):
        return self.min_dist == 0 or marker.get_distance() > self.min_dist

    def _filter_by_time(self, marker):
        if marker.id not in self.det_times:
            self.det_times[marker.id] = time.time()
            return True
        if time.time() - self.det_times[marker.id] < self.det_cd:
            return False
        self.det_times[marker.id] = time.time()
        return True

    def _passes_filters(self, marker):
        return all([f(marker) for f in self.filters])
