#!/usr/bin/env python3
from __future__ import annotations

import ast
import compileall
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TRACKED = {'.env', 'credentials.json', 'fintor.db'}
SECRET_PATTERNS = {
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'openai_key': re.compile(r'\bsk-[A-Za-z0-9_-]{20,}\b'),
    'telegram_token': re.compile(r'\b\d{6,12}:[A-Za-z0-9_-]{25,}\b'),
}


def tracked_files() -> list[str]:
    out = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def local_modules(files: list[str]) -> set[str]:
    modules: set[str] = set()
    for name in files:
        if not name.endswith('.py'):
            continue
        path = Path(name)
        parts = list(path.with_suffix('').parts)
        if parts[-1] == '__init__':
            parts = parts[:-1]
        if parts:
            for i in range(1, len(parts) + 1):
                modules.add('.'.join(parts[:i]))
    return modules


def main() -> int:
    files = tracked_files()
    errors: list[str] = []

    if not compileall.compile_dir(ROOT, quiet=1):
        errors.append('Python compile check failed')

    forbidden = sorted(FORBIDDEN_TRACKED.intersection(files))
    if forbidden:
        errors.append(f'Forbidden tracked files: {forbidden}')

    modules = local_modules(files)
    for name in files:
        if not name.endswith('.py'):
            continue
        path = ROOT / name
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=name)
        except SyntaxError as exc:
            errors.append(f'{name}: syntax error: {exc}')
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                root = node.module.split('.')[0]
                if root in {'keyboards', 'middlewares', 'services', 'states', 'config', 'database'}:
                    if node.module not in modules:
                        errors.append(f'{name}: unresolved local import {node.module}')

    for name in files:
        if name == '.env.example' or not (ROOT / name).is_file():
            continue
        try:
            text = (ROOT / name).read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f'{name}: possible {label}')

    if errors:
        print('PUBLIC SNAPSHOT CHECK: FAIL')
        for error in errors:
            print(f' - {error}')
        return 1

    print('PUBLIC SNAPSHOT CHECK: PASS')
    print(f'Tracked files checked: {len(files)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
