"""
Helper functions that provide general utilities.
"""

def camel_case_to_snake_case(string):
    """
    Example: "RankedList" --> "ranked_list"
    """
    return ''.join(
        [
            '_' + char.lower() if char.isupper()
            else char 
            for char in string
        ]
    ).lstrip('_')


