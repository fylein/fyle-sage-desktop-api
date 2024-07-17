
def format_attribute_name(use_code_in_naming: bool, attribute_name: str, attribute_code: str = None) -> str:
    """
    Format the attribute name based on the use_code_in_naming
    """
    if use_code_in_naming:
        return "{} {}".format(attribute_code, attribute_name)
    return attribute_name
