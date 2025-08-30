import re

def normalize_number(raw: str) -> str:
    
    """
    Normalize a phone number entered either as local (01...) or international (+20...).
    Args:
        raw (str): Raw phone number input.
    Returns:
        str: Normalized phone number or empty string if invalid.
    """
    if not raw:
        return ''
    
    s = raw.strip()
    # Accept spaces, dashes and parentheses and remove them
    s = re.sub(r"[\s\-()]", "", s)

    # If user entered with leading +, keep only digits after +
    if s.startswith("+"):
    # +2010... -> convert to 0 10...
        if s.startswith("+20"):
            s = '0' + s[3:]
        else:
            return "" # not Egyptian country code


    # If user entered international without + (e.g. 2010...), reject for clarity
    if s.startswith("20") and len(s) >= 11:
    # convert 20XXXXXXXXXX -> 0XXXXXXXXXXX if it looks like an Egyptian mobile
        s = '0' + s[2:]

    # Now s should be in local style: start with 0 and length 11
    if re.fullmatch(r"0\d{10}", s):
        return s
    return ""

def validate_egyptian_mobile(local_number: str) -> tuple[bool, str]:
    """
    Validate if the given local number is a valid Egyptian mobile number.
    Args:
        local_number (str): Local phone number starting with 0.
    Returns:
        (bool, str): Tuple of (is_valid, error_message). If valid, error_message is empty.
    """

    if not local_number:
        return False, "Phone number is empty."

    if not re.fullmatch(r"0\d{10}", local_number):
        return False, "Phone number must start with 0 and be 11 digits long."

    # Egyptian mobile prefixes
    prefix = local_number[:3]

    operator_map = {
    '010': 'Vodafone',
    '011': 'Etisalat',
    '012': 'Orange',
    '015': 'WE',
    }

    if prefix not in operator_map:
        return False, "Phone number prefix is not a valid Egyptian mobile operator."
    else:
        return True, operator_map[prefix]