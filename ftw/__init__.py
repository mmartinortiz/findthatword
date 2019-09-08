

def to_alpha(text):
    """Remove non-aphabetic characters and switch to lower case"""
    result = ''
    for letter in text.lower():
        if letter.isalpha():
            result += letter
    return result
