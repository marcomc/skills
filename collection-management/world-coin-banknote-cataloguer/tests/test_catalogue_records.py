"""Behavior tests for the deterministic catalogue helper."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "catalogue_records.py"
SPEC = importlib.util.spec_from_file_location("catalogue_records", SCRIPT)
assert SPEC and SPEC.loader
catalogue_records = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = catalogue_records
SPEC.loader.exec_module(catalogue_records)


def banknote(serial: str) -> dict[str, object]:
    return {
        "id": "BANKNOTE-1",
        "country": "Canada",
        "denomination": 5,
        "currency_code": "CAD",
        "series": 2013,
        "serial": serial,
        "confidence": "HIGH",
    }


def coin(reverse: str = "Common loon") -> dict[str, object]:
    return {
        "id": "COIN-1",
        "country": "Canada",
        "denomination": 1,
        "currency_code": "CAD",
        "series": 2011,
        "obverse": "Queen Elizabeth II",
        "reverse": reverse,
        "issue_name": "Regular issue",
        "confidence": "HIGH",
    }


class CatalogueTests(unittest.TestCase):
    def test_new_banknote_is_inserted(self) -> None:
        result = catalogue_records.classify_banknote(banknote("NEW0001"), [])
        self.assertEqual(result["action"], catalogue_records.ACTION_INSERT)

    def test_exact_banknote_serial_is_skipped(self) -> None:
        result = catalogue_records.classify_banknote(
            banknote("INT4015078"), [{**banknote("INT4015078"), "row": 14}]
        )
        self.assertEqual(result["action"], catalogue_records.ACTION_SKIP_DUPLICATE)
        self.assertEqual(result["existing_row"], 14)

    def test_conflicting_existing_serial_needs_review(self) -> None:
        existing = {**banknote("INT4015078"), "denomination": 10, "row": 14}
        result = catalogue_records.classify_banknote(banknote("INT4015078"), [existing])
        self.assertEqual(result["action"], catalogue_records.ACTION_NEEDS_REVIEW)

    def test_exact_coin_increments_quantity(self) -> None:
        result = catalogue_records.classify_coin(
            coin(), [{**coin(), "row": 8, "quantity": 1}]
        )
        self.assertEqual(result["action"], catalogue_records.ACTION_UPDATE_QUANTITY)
        self.assertEqual(result["new_quantity"], 2)

    def test_batch_coin_quantity_updates_project_per_existing_row(self) -> None:
        first = {**coin(), "id": "COIN-1"}
        second = {**coin(), "id": "COIN-2"}
        different = {**coin("Maple Leaf"), "id": "COIN-3"}
        result = catalogue_records.plan(
            {
                "album_year": 2026,
                "coins": [first, second, different],
                "existing_coins": [
                    {**coin(), "row": 8, "quantity": 1},
                    {**coin("Maple Leaf"), "row": 12, "quantity": 4},
                ],
            }
        )

        self.assertEqual(
            [
                (
                    item["id"],
                    item["existing_row"],
                    item["old_quantity"],
                    item["new_quantity"],
                )
                for item in result["decisions"]
            ],
            [
                ("COIN-1", 8, 1, 2),
                ("COIN-2", 8, 2, 3),
                ("COIN-3", 12, 4, 5),
            ],
        )
        self.assertEqual(
            [
                (
                    item["existing_row"],
                    item["old_quantity"],
                    item["new_quantity"],
                    item["specimen_ids"],
                )
                for item in result["coin_write_operations"]
            ],
            [(8, 1, 3, ["COIN-1", "COIN-2"]), (12, 4, 5, ["COIN-3"])],
        )
        self.assertEqual(
            result["summary"][catalogue_records.ACTION_UPDATE_QUANTITY], 3
        )
        self.assertEqual(
            result["coin_write_summary"][catalogue_records.ACTION_UPDATE_QUANTITY],
            2,
        )

    def test_duplicate_new_coin_specimens_share_one_insert_operation(self) -> None:
        result = catalogue_records.plan(
            {
                "album_year": 2026,
                "coins": [
                    {**coin(), "id": "NEW-1", "issue_name": ""},
                    {**coin(), "id": "NEW-2"},
                    {**coin("Maple Leaf"), "id": "NEW-3"},
                ],
                "existing_coins": [],
            }
        )

        self.assertEqual(
            [item["action"] for item in result["decisions"]],
            [
                catalogue_records.ACTION_INSERT,
                catalogue_records.ACTION_INSERT,
                catalogue_records.ACTION_INSERT,
            ],
        )
        self.assertEqual(
            [item["coin_operation_index"] for item in result["decisions"]],
            [0, 0, 1],
        )
        self.assertEqual(len(result["coin_write_operations"]), 2)
        operation = result["coin_write_operations"][0]
        self.assertEqual(operation["action"], catalogue_records.ACTION_INSERT)
        self.assertEqual(operation["quantity"], 2)
        self.assertEqual(operation["record"]["quantity"], 2)
        self.assertEqual(operation["record"]["issue_name"], "Regular issue")
        self.assertEqual(operation["specimen_ids"], ["NEW-1", "NEW-2"])
        self.assertNotIn("existing_row", operation)
        self.assertEqual(result["coin_write_operations"][1]["quantity"], 1)
        self.assertEqual(
            result["coin_write_operations"][1]["specimen_ids"], ["NEW-3"]
        )

    def test_conflicting_names_for_same_new_coin_issue_require_review(self) -> None:
        result = catalogue_records.plan(
            {
                "album_year": 2026,
                "coins": [
                    {**coin(), "id": "NEW-A", "issue_name": "Issue A"},
                    {**coin(), "id": "NEW-B", "issue_name": "Issue B"},
                ],
                "existing_coins": [],
            }
        )

        self.assertEqual(
            [item["action"] for item in result["decisions"]],
            [catalogue_records.ACTION_NEEDS_REVIEW] * 2,
        )
        self.assertEqual(result["coin_write_operations"], [])
        self.assertEqual(result["coin_write_summary"], {})

    def test_optional_issue_name_does_not_create_duplicate_coin(self) -> None:
        existing = {**coin(), "issue_name": "", "row": 8, "quantity": 1}
        result = catalogue_records.classify_coin(coin(), [existing])
        self.assertEqual(result["action"], catalogue_records.ACTION_UPDATE_QUANTITY)

    def test_same_year_different_commemoratives_stay_distinct(self) -> None:
        first = {
            **coin("Blue Ridge Parkway"),
            "country": "United States",
            "denomination": "25 cents",
            "currency_code": "USD",
            "series": 2015,
            "issue_name": "Blue Ridge Parkway",
        }
        second = {
            **first,
            "reverse": "Bombay Hook National Wildlife Refuge",
            "issue_name": "Bombay Hook",
        }
        result = catalogue_records.classify_coin(second, [{**first, "quantity": 1}])
        self.assertEqual(result["action"], catalogue_records.ACTION_INSERT)

    def test_ambiguous_coin_needs_review(self) -> None:
        ambiguous = {**coin(), "reverse": "", "issue_name": "", "confidence": "LOW"}
        result = catalogue_records.classify_coin(ambiguous, [])
        self.assertEqual(result["action"], catalogue_records.ACTION_NEEDS_REVIEW)

    def test_album_year_stays_numeric(self) -> None:
        headers = ["Album Babbo", "Paese", "Valore"]
        row = catalogue_records.prepare_row(
            headers, {"album_year": 2026, "country": "Canada", "denomination": 5}
        )
        self.assertEqual(row, [2026, "Canada", 5])
        with self.assertRaises(TypeError):
            catalogue_records.prepare_row(headers, {"album_year": "2026"})

    def test_verified_ecuador_currency_correction_is_preserved(self) -> None:
        headers = ["Paese", "Valore", "S.lo", "Codice", "Valuta", "Album Babbo"]
        row = catalogue_records.prepare_row(
            headers,
            {
                "country": "Ecuador",
                "denomination": "5 centavos",
                "currency_symbol": "$",
                "currency_code": "USD",
                "currency_name": "Dollaro statunitense",
                "album_year": 2026,
            },
        )
        self.assertEqual(row[2:5], ["$", "USD", "Dollaro statunitense"])

    def test_pairing_uses_serial_over_changed_position(self) -> None:
        fronts = []
        backs = []
        for index in range(5):
            fronts.append(
                {
                    "id": f"F{index}",
                    "serial": f"SERIAL{index}",
                    "denomination": index + 1,
                    "country": "Canada",
                    "position": str(index),
                }
            )
            back_position = "changed" if index == 2 else str(index)
            backs.append(
                {
                    "id": f"B{index}",
                    "serial": f"SERIAL{index}",
                    "denomination": index + 1,
                    "country": "Canada",
                    "position": back_position,
                }
            )
        backs[2], backs[4] = backs[4], backs[2]
        result = catalogue_records.pair_sides(fronts, backs)
        self.assertEqual(
            [(item["front_id"], item["back_id"]) for item in result],
            [(f"F{i}", f"B{i}") for i in range(5)],
        )

    def test_pairing_rejects_position_only_evidence(self) -> None:
        fronts = [{"id": "F1", "position": "upper-left"}]
        backs = [{"id": "B1", "position": "upper-left"}]
        with self.assertRaises(ValueError):
            catalogue_records.pair_sides(fronts, backs)

    def test_pairing_rejects_position_as_only_discriminator(self) -> None:
        fronts = [
            {
                "id": f"F{index}",
                "country": "Canada",
                "denomination": 5,
                "series": 2013,
                "position": str(index),
            }
            for index in range(2)
        ]
        backs = [
            {
                "id": f"B{index}",
                "country": "Canada",
                "denomination": 5,
                "series": 2013,
                "position": str(index),
            }
            for index in range(2)
        ]
        with self.assertRaises(ValueError):
            catalogue_records.pair_sides(fronts, backs)


if __name__ == "__main__":
    unittest.main()
