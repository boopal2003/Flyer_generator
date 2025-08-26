# tools/encrypt_key.py
# Usage (bash):   python tools/encrypt_key.py <MASTER_KEY> <PLAINTEXT_OPENAI_KEY>
# Usage (pwsh):   python tools/encrypt_key.py $env:MASTER_KEY $env:OPENAI_KEY

import sys
from cryptography.fernet import Fernet

if len(sys.argv) != 3:
    print("Usage: python tools/encrypt_key.py <MASTER_KEY> <OPENAI_KEY>", file=sys.stderr)
    sys.exit(1)

MASTER_KEY = sys.argv[1].encode()
OPENAI_KEY = sys.argv[2].encode()
cipher = Fernet(MASTER_KEY)
print(cipher.encrypt(OPENAI_KEY).decode())
