"""Row-level security for tenant tables and append-only audit/history tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-22

RLS uses the transaction-local setting `app.school_id`, set by the application after
it has resolved the tenant from trusted configuration. FORCE ROW LEVEL SECURITY makes
the policies apply to the table owner too, so the application role cannot bypass them.
If the setting is missing, no tenant rows are visible or writable.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = [
    "academic_years",
    "admission_enquiries",
    "audit_events",
    "bell_periods",
    "calendar_days",
    "classes",
    "evaluation_rubrics",
    "events",
    "fee_heads",
    "login_attempts",
    "roles",
    "school_settings",
    "subjects",
    "users",
    "approval_records",
    "auth_sessions",
    "documents",
    "feedback",
    "guardians",
    "role_permissions",
    "sections",
    "staff_profiles",
    "student_profiles",
    "terms",
    "user_roles",
    "announcements",
    "assessments",
    "attendance_sessions",
    "class_teacher_assignments",
    "complaints",
    "enrollments",
    "fee_structures",
    "invoices",
    "leave_requests",
    "lesson_topics",
    "message_threads",
    "payments",
    "staff_attendance",
    "staff_compensation",
    "staff_duties",
    "student_guardians",
    "teacher_evaluations",
    "teaching_assignments",
    "timetable_entries",
    "attendance_records",
    "complaint_updates",
    "invoice_lines",
    "marks",
    "messages",
    "payment_allocations",
    "refunds",
    "topic_feedback",
    "topic_progress_logs",
    "attendance_record_history",
    "mark_history",
]

APPEND_ONLY_TABLES = ["audit_events", "attendance_record_history", "mark_history", "approval_records"]

TENANT_PREDICATE = "school_id = NULLIF(current_setting('app.school_id', true), '')::uuid"


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation ON {table} USING ({TENANT_PREDICATE}) WITH CHECK ({TENANT_PREDICATE})")

    op.execute(
        """
        CREATE FUNCTION forbid_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = 'insufficient_privilege';
        END $$;
        """
    )
    for table in APPEND_ONLY_TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION forbid_mutation()"
        )


def downgrade() -> None:
    for table in APPEND_ONLY_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_append_only ON {table}")
    op.execute("DROP FUNCTION IF EXISTS forbid_mutation()")
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
