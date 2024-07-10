from num2words import num2words
class NumberToText:
    def __init__(self,number):
        self.number = str(number).split(".")
    def convert(self):
        
        return f"SON : {num2words(self.number[0],lang='es').upper()} CON {self.number[1]}/100 SOLES"
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.__init__(*args, **kwargs)
        return instance.convert()