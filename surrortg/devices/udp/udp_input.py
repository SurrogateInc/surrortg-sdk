from ...inputs import Input


class UdpInput(Input):
    """A base class for all udp-controlled inputs,
    where endpoints need to be updated after constructor
    """

    def __init__(self):
        self.endpoints = {}

    def set_endpoints(self, endpoints):
        """Set endpoints for this input, overriding existing ones.

        :param endpoints: endpoint information with seats as keys
        :type endpoints: dict
        """
        self.endpoints = endpoints
