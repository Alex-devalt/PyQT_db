# Exception - server error
class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


# Error - a required field is missing from the received dictionary.
class ReqFieldMissingError(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле {self.missing_field}.'
