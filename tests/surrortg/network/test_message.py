import unittest

from surrortg.network import Message, MessageValidationError


class MessageTest(unittest.TestCase):
    def test_init(self):
        # test allowed initializations
        Message("event", "dst")
        Message("event", "dst", src="src")
        Message("event", "dst", src=None)
        Message("event", "dst", payload={"foo": "bar"})
        Message("event", "dst", src="src", payload={"foo": "bar"})

        # test wrong types
        with self.assertRaises(MessageValidationError):
            Message(1, "dst", src="src", payload={"foo": "bar"})
        with self.assertRaises(MessageValidationError):
            Message("event", 1, src="src", payload={"foo": "bar"})
        with self.assertRaises(MessageValidationError):
            Message("event", "dst", src=1, payload={"foo": "bar"})
        with self.assertRaises(MessageValidationError):
            Message("event", "dst", src="src", payload=1)

    def test_from_dict(self):
        def _compare(dictionary):
            self.assertEqual(
                vars(Message.from_dict(dictionary)),
                vars(
                    Message(
                        dictionary["event"],
                        dictionary["dst"],
                        src=dictionary.get("src"),
                        payload=dictionary.get("payload", {}),
                    )
                ),
            )

        # test allowed initializations are the same as with regular init
        _compare({"event": "event", "dst": "dst"})
        _compare({"event": "event", "dst": "dst", "src": "src"})
        _compare({"event": "event", "dst": "dst", "src": None})
        _compare({"event": "event", "dst": "dst", "payload": {"foo": "bar"}})
        _compare(
            {
                "event": "event",
                "dst": "dst",
                "src": None,
                "payload": {"foo": "bar"},
            }
        )

        # test wrong types
        with self.assertRaises(MessageValidationError):
            Message.from_dict(
                {
                    "event": 1,
                    "dst": "dst",
                    "src": None,
                    "payload": {"foo": "bar"},
                }
            )
        with self.assertRaises(MessageValidationError):
            Message.from_dict(
                {
                    "event": "event",
                    "dst": 1,
                    "src": None,
                    "payload": {"foo": "bar"},
                }
            )
        with self.assertRaises(MessageValidationError):
            Message.from_dict(
                {
                    "event": "event",
                    "dst": "dst",
                    "src": 1,
                    "payload": {"foo": "bar"},
                }
            )
        with self.assertRaises(MessageValidationError):
            Message.from_dict(
                {"event": "event", "dst": "dst", "src": None, "payload": 1}
            )

    def test_repr(self):
        self.assertEqual(
            repr(Message("event", "dst")),
            (
                "Message(event='event', dst='dst', src=None, seat=0, "
                "payload={}, isAdmin=False)"
            ),
        )
        self.assertEqual(
            repr(Message("event", "dst", src="src", payload={"foo": "bar"})),
            (
                "Message(event='event', dst='dst', src='src', seat=0, "
                "payload={'foo': 'bar'}, isAdmin=False)"
            ),
        )
