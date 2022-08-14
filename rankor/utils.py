"""
Helper functions that provide general utilities.
"""

def camel_case_to_separated_lowercase(string, separator):
    """
    Examples: 
    ("OhNoMyCamelCase", "~")     --> "oh~no~my~camel~case"
    ("ThisWillBeSnakeCase", "_") --> "this_will_be_snake_case"
    ("ThisWillJustBeWords", " ") --> "this will just be words"        
    """
    return ''.join(
        [
            separator + char.lower() if char.isupper()
            else char 
            for char in string
        ]
    ).lstrip(separator)



def model_name_to_instance_name(model_name):
    """
    Example: "RankedList" --> "ranked_list"
    """
    return camel_case_to_separated_lowercase(model_name, "_")



def model_name_to_casual_mention(model_name):
    """
    Example: "RankedList" --> "ranked list"
    """
    return camel_case_to_separated_lowercase(model_name, " ")



def list_is_sorted(checked_list, sorting_key=None, reversed=False):
    """
    Checks if a list is sorted or not, returns True or False
    """
    if sorting_key is None:
        def sorting_key(item):
            return item

    def compare_items(i):
        if reversed:
            return sorting_key(checked_list[i]) >= sorting_key(checked_list[i+1])
        else:
            return sorting_key(checked_list[i]) <= sorting_key(checked_list[i+1])

    last_index = len(checked_list) - 1
    return all( compare_items(i) for i in range(last_index) )

