class SuperClass:
    def __init__(self):
        print("SuperClass __init__")
        super().__init__()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        print("Superclass setter called!")


class MidClassA(SuperClass):
    def __init__(self):
        print("MidClassA __init__")
        super().__init__()

    @SuperClass.value.setter
    def value(self, new_value):
        super(MidClassA, self.__class__).value.__set__(self, new_value)
        print("MidClassA setter called!", MidClassA.__mro__)


class MidClassB(SuperClass):
    def __init__(self):
        print("MidClassB __init__")
        super().__init__()

    @SuperClass.value.setter
    def value(self, new_value):
        super(MidClassB, self.__class__).value.__set__(self, new_value)
        print("MidClassB setter called!", MidClassB.__mro__)


class SubClass(MidClassB, MidClassA):
    def __init__(self):
        print("SubClass __init__")
        super().__init__()

    @SuperClass.value.setter
    def value(self, new_value):
        super(SubClass, self.__class__).value.__set__(self, new_value)
        print("Subclass setter called!", SubClass.__mro__)


obj = SubClass()
obj.value = 42
print(obj.value)

