import hashlib


def generate_hash_pass(text: str) -> str:
    hash_object = hashlib.md5(text.encode())
    return hash_object.hexdigest()
