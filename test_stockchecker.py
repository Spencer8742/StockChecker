import unittest

from stockchecker import PART_NUMBER, parse_pickup


def pickup_response(stores):
    return {
        "body": {
            "PickupMessage": {
                "stores": [
                    {
                        "storeName": name,
                        "city": city,
                        "partsAvailability": availability,
                    }
                    for name, city, availability in stores
                ]
            }
        }
    }


class ParsePickupTest(unittest.TestCase):
    def test_only_available_stores_are_reported(self):
        data = pickup_response([
            ("Evergreen Walk", "South Windsor",
             {PART_NUMBER: {"pickupDisplay": "available", "pickupSearchQuote": "<b>Available</b> Today"}}),
            ("Westfarms", "Farmington",
             {PART_NUMBER: {"pickupDisplay": "unavailable", "pickupSearchQuote": "Currently unavailable"}}),
        ])
        self.assertEqual(parse_pickup(data), [("Evergreen Walk", "South Windsor", "Available Today")])

    def test_empty_availability_means_no_stock(self):
        # This is what Apple returns today when nothing nearby has the part.
        data = pickup_response([("Evergreen Walk", "South Windsor", {}), ("Westfarms", "Farmington", {})])
        self.assertEqual(parse_pickup(data), [])

    def test_other_parts_are_ignored(self):
        data = pickup_response([("Holyoke", "Holyoke", {"MK1F4LL/A": {"pickupDisplay": "available"}})])
        self.assertEqual(parse_pickup(data), [])

    def test_empty_response(self):
        self.assertEqual(parse_pickup({}), [])


if __name__ == "__main__":
    unittest.main()
