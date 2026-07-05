#!/usr/bin/env bash
set -euo pipefail

# wger 2.7+ removed the /api/v2/login/ HTTP endpoint. Obtain the DRF token
# directly via python3 -c + django.setup(), bypassing manage.py entirely so
# no startup messages (system checks, deprecation warnings) appear on stdout.
# sys.stdout.write() emits no trailing newline; host-side 2>/dev/null drops
# any container stderr. The result is the bare 40-char hex token key.
docker compose -f ./.skyramp/sut/docker-compose.testbot.yml exec -T web \
  python3 -c "
import sys, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.main')
import django
django.setup()
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user = User.objects.get(username='admin')
token, _ = Token.objects.get_or_create(user=user)
sys.stdout.write(token.key)
" 2>/dev/null
