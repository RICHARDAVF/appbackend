class HasPassword:
    def __init__(self, password):
        self.password = password
    def hash(self):
        return ''.join(chr(int(i)) for i in  [ str(ord(i)+8) for i in (self.password+'*'*(8-len(self.password))).upper()])
