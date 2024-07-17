
def format_attribute_name(use_code_in_naming: bool, attribute_name: str, attribute_code: str = None) -> str:
    """
    Format the attribute name based on the use_code_in_naming flag
    """
    if use_code_in_naming and attribute_code:
        return "{} {}".format(attribute_code, attribute_name)
    return attribute_name
