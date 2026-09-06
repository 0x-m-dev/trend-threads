#!/usr/bin/env python3
"""Trend Threads — full pipeline runner (scrape → draft → deliver → Discord).

Runs all three scripts sequentially, captures deliver.py output,
sources the bot token from ~/.hermes/.env, and POSTs to Discord.
"""
import json, os, subprocess, sys, urllib.request
from pathlib import Path

HOME = Path.home()
HERMES_ENV = HOME / '.hermes' / '.env'
PROJECT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT / 'scripts'

# --- 1. Source ~/.hermes/.env ---
with open(HERMES_ENV) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, _, v = line.partition('=')
        v = v.strip('"').strip("'")
        os.environ.setdefault(k, v)

token = os.environ.get('DISCORD_BOT_TOKEN')
if not token:
    print("ERROR: DISCORD_BOT_TOKEN not found in ~/.hermes/.env", file=sys.stderr)
    sys.exit(1)

# --- 2. Run deliver.py ---
result = subprocess.run([sys.executable, str(SCRIPTS / 'deliver.py')],
                        capture_output=True, text=True, cwd=str(PROJECT))
if result.returncode != 0:
    print(f"deliver.py failed: {result.stderr}", file=sys.stderr)
    sys.exit(1)

message = result.stdout.strip()

# --- 3. POST to Discord ---
payload = json.dumps({'content': message, 'allowed_mentions': {'parse': []}}).encode()
req = urllib.request.Request(
    'https://discord.com/api/v10/channels/1545903101024796762/messages',
    data=payload,
    headers={
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json',
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as r:
        body = json.loads(r.read().decode())
    print(f"Discord POST OK — message_id: {body.get('id')}")
except urllib.error.HTTPError as e:
    print(f"Discord POST FAILED {e.code}: {e.read().decode()}", file=sys.stderr)
    sys.exit(1)
