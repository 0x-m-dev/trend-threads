#!/usr/bin/env python3
"""Post a deliver.py message to Discord."""
import sys, json, os, urllib.request

# Source ~/.hermes/.env for DISCORD_BOT_TOKEN
env_path = os.path.expanduser('~/.hermes/.env')
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, _, v = line.partition('=')
        v = v.strip('"').strip("'")
        os.environ.setdefault(k, v)

token = os.environ.get('DISCORD_BOT_TOKEN', '')
if not token:
    print('ERROR: DISCORD_BOT_TOKEN not found in ~/.hermes/.env', file=sys.stderr)
    sys.exit(1)

content = sys.stdin.read().strip()
payload = json.dumps({'content': content, 'allowed_mentions': {'parse': []}}).encode()

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
    print(f'Discord POST OK — message_id: {body.get("id")}')
except urllib.error.HTTPError as e:
    print(f'Discord POST FAILED {e.code}: {e.read().decode()}', file=sys.stderr)
    sys.exit(1)
