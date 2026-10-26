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
