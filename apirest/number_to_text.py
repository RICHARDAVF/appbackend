from num2words import num2words
class NumberToText:
    def __init__(self,number):
        self.number = number
    def convert(self):
        part_int = int(self.number)
        part_decimal = int(self.number-int(self.number))
        return f"SON : {num2words(part_int,lang='es').upper()} CON {part_decimal}/100 SOLES"
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.__init__(*args, **kwargs)
        return instance.convert()