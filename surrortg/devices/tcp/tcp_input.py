from surrortg.inputs import Input


class TcpInput(Input):
    """A base class for all tcp-controlled inputs,
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
