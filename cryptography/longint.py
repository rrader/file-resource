from itertools import dropwhile

BASE = 10
DIGITS = 4

class LongInt(object):
    def __init__(self, number=None, base=BASE, digits=DIGITS):
        self._base = base
        self._digits = digits
        self._data = [0 for _ in range(digits)]
        self._neg = False

        if number:
            self.copy_from(number)

    def parse_int(self, number):
        self._data = [0 for _ in range(self._digits)]
        i = 0
        if number < 0:
            self._neg = True
        number = abs(number)
        while number > 0:
            self._data[i] = number % self._base
            number //= self._base
            i += 1
        if self._neg:
            self.__neg__()

    def copy_from(self, number):
        if isinstance(number, int):
            self.parse_int(number)
        elif isinstance(number, LongInt):
            self._base = number._base
            self._digits = number._digits
            self._data = number._data
            self._neg = number._neg
        else:
            raise TypeError()

    @staticmethod
    def encode(number, base=BASE, digits=DIGITS):
        if isinstance(number, int):
            return LongInt(number, base, digits)
        elif isinstance(number, LongInt):
            assert number._base == base
            assert number._digits == digits
            return number
        else:
            raise TypeError()

    def add(self, other):
        other = LongInt.encode(other)
        carry = 0
        for i in range(self._digits):
            xsum = self[i] + other[i] + carry
            self[i] = (xsum % self._base)
            carry = xsum // self._base
        self._neg = self._neg ^ other._neg ^ bool(carry)

    def sub(self, other):
        other = LongInt.encode(other)
        self.add(-other)

    def negate(self):
        self._neg = not self._neg
        for i in range(self._digits):
            self._data[i] = (self._base - 1) - self._data[i]
        self.add(1)

    def effective_digits(self):
        return len(list(dropwhile(lambda x: x == 0, reversed(self._data))))

    def mul(self, other):
        other = LongInt.encode(other)
        res = [0 for _ in range(self._digits)]
        for i in range(self.effective_digits()):
            carry = 0
            for j in range(other.effective_digits()):
                cur = res[i + j] + self[i] * other[j] + carry
                res[i + j] = cur % self._base
                carry = cur // self._base
            j = other.effective_digits()
            while carry:
                cur = res[i + j] + self[i] * other[j] + carry
                res[i + j] = cur % self._base
                carry = cur // self._base
                j += 1

        self._neg = self._neg ^ other._neg
        self._data = res

    def __str__(self):
        neg = '-<2c>' if self._neg else ''
        return neg + '.'.join([str(i) for i in reversed(self._data)])

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __add__(self, other):
        result = LongInt(self)
        result.add(other)
        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __neg__(self):
        result = LongInt(self)
        result.negate()
        return result

    def __sub__(self, other):
        result = LongInt(self)
        result.sub(other)
        return result

    def __rsub__(self, other):
        result = LongInt(other)
        result.sub(self)
        return result

    def __mul__(self, other):
        result = LongInt(self)
        result.mul(other)
        return result

    def __rmul__(self, other):
        result = LongInt(self)
        result.mul(other)
        return result

    def __pow__(self, power, modulo=None):
        result = LongInt(self)
        for i in range(power - 1):
            result.mul(self)
        if modulo:
            result = result % modulo
        return result

    def __mod__(self, other):
        result = LongInt(self)
        assert result._neg == False
        while not result._neg:
            result.sub(other)
        result.add(other)
        return result


if __name__ == "__main__":
    # print( LongInt(-80) - LongInt(90))
    print(pow(LongInt(13), 2, 2))
    # print(LongInt(3).effective_digits())
    # print( 353 -499 )
    # print(-(-LongInt(12)))
