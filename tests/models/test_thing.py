from rankor.models import Thing, PyObjectId
from pydantic import ValidationError, AnyUrl


def test_initialization():
    assert isinstance(  Thing(name = "The Terminator", 
                              image_url = "https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg",
                              other_data = {"director":"James Cameron", "year":1982},
                              _id = PyObjectId("12345678901234567890abcd")
                             ),
                        Thing) is True, "Initialization failed"


def test_initialization_without_id():
    assert isinstance(  Thing(name = "Aliens", 
                              image_url = "https://m.media-amazon.com/images/I/91kkGWtyqTL._AC_SL1500_.jpg",
                             ),
                        Thing) is True, "Initialization failed"    


def test_validation_error_on_missing_field():
    try:
        t = Thing(image_url = "https://m.media-amazon.com/images/I/91kkGWtyqTL._AC_SL1500_.jpg")
    except ValidationError as error:
        error_info = error.errors()[0]
        assert error_info["msg"] == "field required", "Incorrect ValidationError msg"
        assert error_info["type"] == "value_error.missing", "Incorrect ValidationError type"
    else:
        raise AssertionError("No ValidationError thrown in a case of value_error.missing")


def test_validation_error_on_incorrect_field_type():
    try:
        t = Thing(name = "Test Thing",
                  image_url = "91kkGWtyqTL._AC_SL1500_.jpg")
    except ValidationError as error:
        error_info = error.errors()[0]
        assert error_info["msg"] == "invalid or missing URL scheme", "Incorrect ValidationError msg"
        assert error_info["type"] == "value_error.url.scheme", "Incorrect ValidationError type"
    else:
        raise AssertionError("No ValidationError thrown in a case of value_error.missing")


def test_validation_error_on_invalid_bson_id():
    try:
        t = Thing(name = "Test Thing",
                  _id = "12345678901234567890abcdkkk9976sms")
    except ValidationError as error:
        error_info = error.errors()[0]
        assert error_info["msg"] == "Not a valid bson ObjectId, it must be a 24 character hex string", "Incorrect ValidationError msg"
        assert error_info["type"] == "value_error", "Incorrect ValidationError type"
    else:
        raise AssertionError("No ValidationError thrown in a case of invalid bson ObjectId")


def test_dict_encoding_for_bson_conversion():
    terminator = Thing(name = "The Terminator", 
                       image_url = "https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg",
                       other_data = {"director":"James Cameron", "year":1982},
                       _id = PyObjectId("12345678901234567890abcd"))
    assert terminator.to_bsonable_dict() == {'_id': PyObjectId('12345678901234567890abcd'), 
                                    'name': 'The Terminator', 
                                    'image_url': AnyUrl(url='https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg',
                                                        scheme='https'),
                                    'other_data': {'director': 'James Cameron', 'year': 1982}
                                   }, "Dict encoding (for pymongo to convert to bson) failure"


def test_json_encoding():
    aliens = Thing(name = "Aliens",
                   image_url = "https://m.media-amazon.com/images/I/91kkGWtyqTL._AC_SL1500_.jpg",
                   _id = PyObjectId("12345678901234567890ffff"),
                   other_data = {"director": "James Cameron"})
    expected_json = """{
  "id": "12345678901234567890ffff",
  "image_url": "https://m.media-amazon.com/images/I/91kkGWtyqTL._AC_SL1500_.jpg",
  "name": "Aliens",
  "other_data": {
    "director": "James Cameron"
  }
}"""
    assert aliens.to_json() == expected_json, f"Json encoding failed {type(aliens.to_json())}"


def run_all_thing_tests():
    test_initialization()
    test_initialization_without_id()
    test_validation_error_on_missing_field()
    test_validation_error_on_incorrect_field_type()
    test_validation_error_on_invalid_bson_id()
    test_dict_encoding_for_bson_conversion()
    test_json_encoding()



if __name__ == '__main__':

    run_all_thing_tests()
