#!/usr/bin/env bash
# Creates the local development + test databases and a NON-superuser application role.
# The app role must not be a superuser: superusers bypass PostgreSQL row-level security.
set -euo pipefail
APP_ROLE="${APP_ROLE:-school_app}"
APP_PASSWORD="${APP_PASSWORD:-school_app_dev_password}"
run_psql() { if [ "$(id -u)" = "0" ]; then su postgres -c "psql -v ON_ERROR_STOP=1 -qtAc \"$1\""; else sudo -u postgres psql -v ON_ERROR_STOP=1 -qtAc "$1"; fi; }
if [ -z "$(run_psql "SELECT 1 FROM pg_roles WHERE rolname='${APP_ROLE}'")" ]; then
  run_psql "CREATE ROLE ${APP_ROLE} LOGIN PASSWORD '${APP_PASSWORD}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS"
fi
for DB in school_erp school_erp_test school_erp_e2e; do
  if [ -z "$(run_psql "SELECT 1 FROM pg_database WHERE datname='${DB}'")" ]; then
    run_psql "CREATE DATABASE ${DB} OWNER ${APP_ROLE}"
  fi
done
echo "Databases ready: school_erp, school_erp_test, school_erp_e2e (role: ${APP_ROLE})"
