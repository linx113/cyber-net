#!/bin/sh
set -eu

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
main_dump="/backups/cybernet-main-${stamp}.sql"
logs_dump="/backups/cybernet-logs-${stamp}.sql"

trap 'rm -f "$main_dump" "$logs_dump"' EXIT

export PGPASSWORD="${POSTGRES_PASSWORD}"
pg_dump --host postgres-main --username cybernet --dbname cybernet \
  --no-owner --no-acl --file "$main_dump"
pg_dump --host postgres-logs --username cybernet --dbname cybernet_logs \
  --no-owner --no-acl --file "$logs_dump"

gzip "$main_dump" "$logs_dump"
trap - EXIT
printf 'Database backups created in /backups at %s\n' "$stamp"
