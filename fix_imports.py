import os
import re

backend = os.path.join(os.path.dirname(__file__), 'backend')

replacements = [
    (r'^from Aservices\.', 'from services.'),
    (r'^from Brepositories\.', 'from repositories.'),
    (r'^import Aservices\.', 'import services.'),
    (r'^import Brepositories\.', 'import repositories.'),
]

for root, dirs, files in os.walk(backend):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = content
        for pattern, replacement in replacements:
            new_content = re.sub(pattern, replacement, new_content, flags=re.MULTILINE)
        if new_content != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Corregido: {fpath}")

print("Listo.")