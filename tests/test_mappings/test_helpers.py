from apps.mappings.helpers import format_attribute_name


def test_format_attribute_name():
    # Test case 1: use_code_in_naming is True and attribute_code is not None
    result = format_attribute_name(True, "attribute_name", "attribute_code")
    assert result == "attribute_code attribute_name"

    # Test case 2: use_code_in_naming is True but attribute_code is None
    result = format_attribute_name(True, "attribute_name", None)
    assert result == "attribute_name"

    # Test case 3: use_code_in_naming is False and attribute_code is not None
    result = format_attribute_name(False, "attribute_name", "attribute_code")
    assert result == "attribute_name"

    # Test case 4: use_code_in_naming is False and attribute_code is None
    result = format_attribute_name(False, "attribute_name", None)
    assert result == "attribute_name"
