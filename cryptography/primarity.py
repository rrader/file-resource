import random

TEST_CYCLES = 10


def is_witness(a, t, s, n):
    if pow(a, t, n) == 1:
        return False
    for i in range(s):
        if pow(a, 2 ** i * t, n) == n - 1:
            return False
    return True


def rabin_test(n):
    """Rabin test
    """
    assert n >= 2
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    s = 0
    t = n - 1
    while True:
        d, rem = t // 2, t % 2
        if rem == 1:
            break
        s += 1
        t = d
    assert(2 ** s * t == n - 1)

    for i in range(TEST_CYCLES):
        a = random.randrange(2, n)
        if is_witness(a, t, s, n):
            return False

    return True

def get_prime(bits=128):
    while True:
        number = random.getrandbits(bits)
        if rabin_test(number):
            return number

if __name__ == "__main__":
    A = get_prime()
    print(A, 'is prime:', rabin_test(A))
