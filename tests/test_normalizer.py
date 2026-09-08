from src.normalizer import normalize_value, values_equivalent


def test_currency_scale_equivalence():
    assert values_equivalent(normalize_value("$10M"), normalize_value("USD 10,000,000"))


def test_crore_and_million_equivalence():
    assert values_equivalent(normalize_value("₹81,415.38 million"), normalize_value("₹8,141.538 crore"))


def test_measurement_conversion():
    assert values_equivalent(normalize_value("1", "km"), normalize_value("1000", "m"))


def test_percentage_normalization():
    result = normalize_value("12.5%")
    assert result.value == "12.5" and result.unit == "%"
