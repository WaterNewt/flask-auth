import hashlib
import random
import string

def generate_key(username:str):
    characters = string.ascii_letters + string.digits
    key = ''.join(random.choice(characters) for _ in range(32))
    key+=username
    return key

def md5_hash(input_string):
    # Encode the input string as bytes
    input_bytes = input_string.encode('utf-8')
    
    # Create an MD5 hash object
    md5_hash_object = hashlib.md5()
    
    # Update the hash object with the input bytes
    md5_hash_object.update(input_bytes)
    
    # Get the hexadecimal representation of the hash
    md5_hash_hex = md5_hash_object.hexdigest()
    
    return md5_hash_hex