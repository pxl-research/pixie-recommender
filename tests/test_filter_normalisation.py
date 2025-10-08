import unittest

from pixie.core.llms.azure_filter_llm import AzureFilterLLM


class FilterNormalisationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.filter_llm = AzureFilterLLM(
            api_version="2024-01-01",
            api_endpoint="https://example.com",
            api_key="dummy",
            model_version="dummy-model",
        )

    def test_range_filter_string_values_are_converted(self) -> None:
        filters = [
            {
                "name": "prijs",
                "type": "range",
                "min_value": "200",
                "max_value": "828,93 euro",
            }
        ]
        attribute = {"name": "prijs", "type": "numeric"}

        result = self.filter_llm._normalise_filters(filters, attribute)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["min_value"], 200.0)
        self.assertAlmostEqual(result[0]["max_value"], 828.93, places=2)

    def test_exact_numeric_filter_from_string(self) -> None:
        filters = [{"name": "prijs", "type": "exact", "value": "€299"}]
        attribute = {"name": "prijs", "type": "numeric"}

        result = self.filter_llm._normalise_filters(filters, attribute)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["value"], 299.0)

    def test_boolean_filter_from_text(self) -> None:
        filters = [{"name": "beschikbaar", "type": "exact", "value": "nee"}]
        attribute = {"name": "beschikbaar", "type": "boolean"}

        result = self.filter_llm._normalise_filters(filters, attribute)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["value"])

    def test_invalid_numeric_range_is_dropped(self) -> None:
        filters = [{"name": "prijs", "type": "range", "min_value": "abc"}]
        attribute = {"name": "prijs", "type": "numeric"}

        result = self.filter_llm._normalise_filters(filters, attribute)

        self.assertEqual(result, [])

    def test_build_filters_without_llm_returns_empty(self) -> None:
        attribute = {"name": "prijs", "type": "numeric"}

        result = self.filter_llm.build_filters("ongeveer 250 euro", attribute)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
