class Superclass:
    def __init__(self):
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        print("Superclass setter called!")
        # Additional manipulation in the superclass
        # ...


class Subclass(Superclass):
    @Superclass.value.setter
    def value(self, new_value):
        # Additional manipulation in the subclass
        # ...
        super(Subclass, Subclass).value.__set__(self, new_value)  # Calling the superclass's setter
        print("Subclass setter called!")


obj = Subclass()
obj.value = 42
print(obj.value)
