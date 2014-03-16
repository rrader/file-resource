from pydes import pyDes
from pydes.pyDes import PAD_NORMAL

if __name__ == "__main__":
    data = 'hello world'
    k = pyDes.des(b'MYKEY123', pyDes.CBC, '\0\0\0\0\0\0\0\0', b' ')
    encrypted = k.encrypt(data)
    print(encrypted)
    decrypted = k.decrypt(encrypted)
    print(decrypted)
