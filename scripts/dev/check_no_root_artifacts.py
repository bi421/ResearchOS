#!/usr/bin/env python3
"""Pre-commit hook: prevent artifact files in repo root."""

import os
import sys

ROOT = os.getcwd()
BAD_EXTENSIONS = (".db", ".csv", ".json", ".txt", ".log")
artifacts = [
    f
    for f in os.listdir(ROOT)
    if f.endswith(BAD_EXTENSIONS) and os.path.isfile(os.path.join(ROOT, f))
]

if artifacts:
    for a in artifacts:
        print(f"REJECTED: artifact file in root: {a}")
    sys.exit(1)

print("Root is clean")
