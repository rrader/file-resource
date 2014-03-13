from collections import namedtuple
import random
from primarity import get_prime

keys = namedtuple('rsakey', ['private', 'public'])

BITS = 16


def egcd(a, b):
    if b == 0:
        return a, 1, 0
    else:
        d, x, y = egcd(b, a % b)
        return d, y, x - y * (a // b)


def get_coprime(number):
    e = random.randint(2, number)
    while egcd(e, number)[0] != 1:
        e = random.randint(2, number)
    return e


def generate_rsa_keys():
    p = get_prime(BITS)
    q = get_prime(BITS)
    n = p*q
    phi = (p-1)*(q-1) # euler's formula

    e = get_coprime(phi)

    _, x, q = egcd(e, phi)
    d = (x + phi) % phi

    return keys(private=(n, d), public=(n, e))


if __name__ == "__main__":
    keys = generate_rsa_keys()
    print(keys)
