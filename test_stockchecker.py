import unittest

from stockchecker import PART_NUMBER, parse_availability


def response(stores=(), delivery=None):
    return {
        "body": {
            "content": {
                "pickupMessage": {
                    "stores": [
                        {
                            "storeName": name,
                            "city": city,
                            "partsAvailability": {
                                PART_NUMBER: {"pickupDisplay": display, "pickupSearchQuote": quote}
                            },
                        }
                        for name, city, display, quote in stores
                    ]
                },
                "deliveryMessage": {PART_NUMBER: delivery} if delivery is not None else {},
            }
        }
    }


class ParseAvailabilityTest(unittest.TestCase):
    def test_only_available_stores_are_reported(self):
        data = response(stores=[
            ("Fifth Avenue", "New York", "available", "Available Today"),
            ("SoHo", "New York", "unavailable", "Currently unavailable"),
        ])
        self.assertEqual(
            parse_availability(data)["stores"],
            [("Fifth Avenue", "New York", "Available Today")],
        )

    def test_delivery_quote(self):
        data = response(delivery={
            "regular": {
                "buyability": {"isBuyable": True},
                "deliveryOptionMessages": [{"displayName": "Delivers Nov 7 - Nov 14"}],
            }
        })
        self.assertEqual(parse_availability(data)["delivery"], "Delivers Nov 7 - Nov 14")

    def test_not_buyable(self):
        data = response(delivery={"regular": {"buyability": {"isBuyable": False}}})
        self.assertEqual(parse_availability(data)["delivery"], "Not buyable online")

    def test_compact_fallback(self):
        data = response(delivery={"regular": {}, "compact": {"quote": "Ships in 3-4 weeks"}})
        self.assertEqual(parse_availability(data)["delivery"], "Ships in 3-4 weeks")

    def test_empty_response(self):
        self.assertEqual(parse_availability({}), {"stores": [], "delivery": None})


if __name__ == "__main__":
    unittest.main()
