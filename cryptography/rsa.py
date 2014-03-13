from collections import namedtuple
import random
from primarity import get_prime

keys = namedtuple('rsakey', ['private', 'public'])

BITS = 16  # 512
BYTES = (BITS // 8)*2


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


def blocks(seq, block_size=BYTES):
    return map(lambda x: bytes(x), zip(*[iter(seq)]*block_size))


def encrypt_block(block, public_key):
    return pow(block, public_key[1], public_key[0])


def decrypt_block(block, private_key):
    return pow(block, private_key[1], private_key[0])


def encrypt(data, public_key):
    message = bytearray(data, 'utf-8')
    while len(message) % BYTES > 0:
        message.append(0)

    encrypted = []
    for block in blocks(message):
        block_i = int.from_bytes(block, byteorder='big')
        encrypted_block = encrypt_block(block_i, public_key)
        encrypted_block_bytes = int.to_bytes(encrypted_block, byteorder='big', length=BYTES)
        encrypted.append(encrypted_block_bytes)
        print("encrypted block", block_i, '->', encrypted_block, encrypted_block_bytes)
    return b''.join(encrypted)


def decrypt(data, private_key):
    decrypted = []
    for block in blocks(data):
        block_i = int.from_bytes(block, byteorder='big')
        decrypted_block = decrypt_block(block_i, private_key)
        print("block to decrypt", block_i, '->', decrypted_block, block)
        decrypted_block_bytes = int.to_bytes(decrypted_block, byteorder='big', length=BYTES)
        decrypted.append(decrypted_block_bytes)
    print(decrypted)


if __name__ == "__main__":
    keys = generate_rsa_keys()
    print(keys)

    encrypted = encrypt('hello', keys.public)
    print(encrypted, len(encrypted))
    decrypted = decrypt(encrypted, keys.private)

    x = encrypt_block(1751477356, keys.public)
    print(decrypt_block(x, keys.private))
