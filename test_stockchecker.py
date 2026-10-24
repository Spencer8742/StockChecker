import unittest

from stockchecker import PART_NUMBER, parse_delivery, parse_pickup


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


def delivery_response(regular):
    return {"body": {"content": {"deliveryMessage": {PART_NUMBER: {"regular": regular}}}}}


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


class ParseDeliveryTest(unittest.TestCase):
    def test_ships_message(self):
        data = delivery_response({
            "buyability": {"isBuyable": True},
            "stickyMessageSTH": 'Ships <span class="bold">Mon, Jan 25</span>',
            "deliveryOptionMessages": [{"displayName": "Mon, Jan 25 — Free"}],
        })
        self.assertEqual(parse_delivery(data), "Ships Mon, Jan 25")

    def test_falls_back_to_delivery_option(self):
        data = delivery_response({"deliveryOptionMessages": [{"displayName": "Mon, Jan 25 — Free"}]})
        self.assertEqual(parse_delivery(data), "Mon, Jan 25 — Free")

    def test_not_buyable(self):
        data = delivery_response({"buyability": {"isBuyable": False}})
        self.assertEqual(parse_delivery(data), "Not buyable online")

    def test_empty_response(self):
        self.assertIsNone(parse_delivery({}))


if __name__ == "__main__":
    unittest.main()
