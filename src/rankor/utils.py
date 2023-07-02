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



def casual_mention_to_model_name(casual_mention):
    """
    Example: "ranked list" --> "RankedList"
    """
    return ''.join( 
        [
            word.capitalize() 
            for word in casual_mention.split(" ")
        ]
    )



def append_or_update_batch_number(source_string, 
                                  batch_no,
                                  batch_denoter=" | batch ",\
                                  batch_no_format="{:03d}"):
    """
    Example: "The Terminator" --> "The Terminator | batch 001"
    Example: "The Terminator | batch 005" --> "The Terminator | batch 006"
    """
    return ''.join(
        [
            source_string.rsplit(batch_denoter,1)[0],
            batch_denoter,
            batch_no_format.format(batch_no)
        ]
    )



def list_is_sorted(checked_list, key=lambda x: x, reverse=False):
    """
    Checks if a list is sorted or not, returns True or False
    Complexity is O(n) in the worst case scenario: a sorted list
    """
    def elements_out_of_order(prev_index, elem):
        if reverse:
            return key(checked_list[prev_index]) < key(elem)
        else:
            return key(checked_list[prev_index]) > key(elem) 

    for prev_index, elem in enumerate(checked_list[1:]):
        # prev_index is the index of the previous element
        # in the first iteration, prev_index is 0, elem is checked_list[1]
        # in the second iteration, prev_index is 1, elem is checked_list[2]
        # etc.        
        if elements_out_of_order(prev_index, elem): 
            return False
    return True
