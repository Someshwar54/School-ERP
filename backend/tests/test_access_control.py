"""Authorisation boundaries: every check here is enforced server-side, independent of the UI."""

from sqlalchemy import select

from app.models import Complaint, LessonTopic, MessageThread, Section, StudentProfile
from tests.conftest import as_user, tenant_session


def _id_of(model, **where):  # type: ignore[no-untyped-def]
    s = tenant_session("demo")
    try:
        return str(s.scalar(select(model.id).filter_by(**where)))
    finally:
        s.close()


def _section(label: str) -> str:
    from app.models import SchoolClass

    grade, name = label.split("-")
    s = tenant_session("demo")
    try:
        return str(
            s.scalar(
                select(Section.id)
                .join(SchoolClass, SchoolClass.id == Section.class_id)
                .where(SchoolClass.grade_number == int(grade), Section.name == name)
            )
        )
    finally:
        s.close()


# ---- students -------------------------------------------------------------------------------------------------------
def test_student_cannot_reach_other_students_or_staff_areas() -> None:
    c = as_user("student", "STU0001")
    other = _id_of(StudentProfile, student_code="STU0002")
    assert c.get(f"/finance/students/{other}/ledger").status_code == 403
    for path in [
        "/teacher/dashboard",
        "/staff/dashboard",
        "/hr/staff",
        "/hr/payroll",
        "/management/overview",
        "/management/audit",
        "/finance/invoices",
    ]:
        assert c.get(path).status_code == 403, path


def test_student_endpoints_never_accept_a_student_id() -> None:
    """Student data endpoints are keyed on the session; query parameters cannot redirect them."""
    c = as_user("student", "STU0001")
    other = _id_of(StudentProfile, student_code="STU0002")
    r = c.get(f"/student/profile?student_id={other}")
    assert r.json()["student_code"] == "STU0001"
    fees = c.get(f"/student/fees?student_id={other}").json()
    own_invoices = {i["invoice_no"] for i in fees["invoices"]}
    other_fees = as_user("student", "STU0002").get("/student/fees").json()
    assert own_invoices.isdisjoint({i["invoice_no"] for i in other_fees["invoices"]})


def test_student_cannot_read_another_students_conversation() -> None:
    s = tenant_session("demo")
    try:
        thread = s.scalar(select(MessageThread))
        owner_code = s.scalar(select(StudentProfile.student_code).where(StudentProfile.id == thread.student_id))
    finally:
        s.close()
    assert as_user("student", owner_code).get(f"/student/messages/{thread.id}").status_code == 200
    assert as_user("student", "STU0005").get(f"/student/messages/{thread.id}").status_code == 404


def test_student_cannot_message_unassigned_teacher() -> None:
    c = as_user("student", "STU0001")  # Grade 6-A
    teacher_9a_math = _id_of(__import__("app.models", fromlist=["StaffProfile"]).StaffProfile, staff_code="EMP1001")
    r = c.post("/student/messages", {"staff_id": teacher_9a_math, "subject": "Hello", "body": "Hi"})
    assert r.status_code == 403


def test_student_cannot_give_feedback_on_another_class_topic() -> None:
    topic = _id_of(LessonTopic, section_id=_section("10-B"), sequence=1)
    r = as_user("student", "STU0001").post(f"/student/topics/{topic}/feedback", {"understanding": 3})
    assert r.status_code == 404


def test_unpublished_results_are_hidden_from_students() -> None:
    results = as_user("student", "STU0181").get("/student/results").json()
    names = {e["assessment"] for e in results["exams"]}
    assert "Unit Test 3" not in names  # seeded as unpublished
    assert "Half-Yearly Examination" in names


def test_holidays_are_not_counted_as_absences() -> None:
    data = as_user("student", "STU0181").get("/student/attendance?month=2026-08").json()
    aug15 = next(d for d in data["days"] if d["day"] == "2026-08-15")
    assert aug15["status"] == "holiday"
    assert all(d["status"] != "absent" for d in data["days"] if d["status"] in ("holiday", "weekly_off"))


# ---- teachers -------------------------------------------------------------------------------------------------------
def test_teacher_cannot_access_unrelated_classes() -> None:
    c = as_user("staff", "EMP1001")  # Maths for 8-B..10-B, class teacher of 9-A
    unrelated = _section("6-A")
    assert c.get(f"/teacher/sections/{unrelated}/students").status_code == 403
    assert c.get(f"/teacher/class/{unrelated}").status_code == 403
    assert c.get(f"/teacher/attendance?section_id={unrelated}&day=2026-10-21").status_code == 403
    math = c.get("/teacher/assignments").json()[0]["subject_id"]
    assert c.get(f"/teacher/assessments?section_id={unrelated}&subject_id={math}").status_code == 403
    body = {
        "section_id": unrelated,
        "day": "2026-10-21",
        "period_no": 0,
        "records": [{"student_id": _id_of(StudentProfile, student_code="STU0001"), "status": "absent"}],
    }
    assert c.put("/teacher/attendance", body).status_code == 403


def test_teacher_cannot_edit_marks_for_unassigned_assessment() -> None:
    from app.models import Assessment, Subject

    s = tenant_session("demo")
    try:
        eng = s.scalar(select(Subject.id).where(Subject.code == "ENG"))
        a = s.scalar(select(Assessment.id).where(Assessment.section_id == _section("9-A"), Assessment.subject_id == eng))
    finally:
        s.close()
    c = as_user("staff", "EMP1001")  # teaches Maths, not English, in 9-A
    assert c.get(f"/teacher/assessments/{a}/marks").status_code == 403
    r = c.put(
        f"/teacher/assessments/{a}/marks",
        {"marks": [{"student_id": _id_of(StudentProfile, student_code="STU0181"), "marks_obtained": "10"}]},
    )
    assert r.status_code == 403


def test_subject_teacher_without_class_cannot_take_daily_register() -> None:
    c = as_user("staff", "EMP1002")  # Science teacher, no class-teacher assignment
    me = c.get("/auth/me").json()["workspace"]
    assert me["class_teacher_of"] == [] and "class" not in me["modules"]
    sec = c.get("/teacher/assignments").json()[0]["section_id"]
    assert c.get(f"/teacher/attendance?section_id={sec}&day=2026-10-21&period_no=0").status_code == 403


def test_class_teacher_gets_class_workspace_from_assignment() -> None:
    me = as_user("staff", "EMP1001").get("/auth/me").json()["workspace"]
    assert me["is_teacher"] and "class" in me["modules"]
    assert [c["section"] for c in me["class_teacher_of"]] == ["9-A"]


def test_teacher_sees_only_assigned_non_confidential_complaints() -> None:
    items = as_user("staff", "EMP1001").get("/teacher/complaints").json()
    assert items and all(not c["is_confidential"] for c in items)
    s = tenant_session("demo")
    try:
        confidential = s.scalar(select(Complaint.id).where(Complaint.is_confidential.is_(True)))
    finally:
        s.close()
    r = as_user("staff", "EMP1001").post(f"/teacher/complaints/{confidential}/update", {"note": "peek"})
    assert r.status_code == 404


# ---- non-teaching staff ---------------------------------------------------------------------------------------------
def test_ordinary_staff_cannot_reach_management_or_sensitive_data() -> None:
    c = as_user("staff", "EMP2005")  # office assistant
    ws = c.get("/auth/me").json()["workspace"]
    assert not ws["is_teacher"]
    assert {"finance", "hr", "marks", "attendance", "class"}.isdisjoint(ws["modules"])
    for path in [
        "/teacher/dashboard",
        "/finance/summary",
        "/finance/invoices",
        "/hr/staff",
        "/hr/payroll",
        "/management/overview",
        "/management/complaints",
        "/management/audit",
    ]:
        assert c.get(path).status_code == 403, path


def test_finance_staff_get_only_finance_module() -> None:
    c = as_user("staff", "EMP2001")
    ws = c.get("/auth/me").json()["workspace"]
    assert "finance" in ws["modules"] and "hr" not in ws["modules"]
    assert c.get("/finance/invoices").status_code == 200
    assert c.get("/hr/payroll").status_code == 403


# ---- management -----------------------------------------------------------------------------------------------------
def test_director_portal_alone_grants_nothing() -> None:
    board = as_user("director", "DIR003")
    assert board.get("/management/overview").status_code == 200
    assert board.get("/hr/payroll").status_code == 403
    assert board.get("/finance/invoices").status_code == 403
    assert board.get("/management/audit").status_code == 403
    complaints = board.get("/management/complaints").json()
    assert complaints["items"] is None  # summary only, no individual or confidential complaints
    assert board.post("/management/assessments/00000000-0000-0000-0000-000000000000/publish").status_code == 403


def test_confidential_complaints_visible_only_with_permission() -> None:
    principal = as_user("director", "DIR002").get("/management/complaints").json()
    assert any(c["is_confidential"] for c in principal["items"])


def test_technical_admin_has_no_business_data() -> None:
    c = as_user("director", "DIR008")
    assert c.get("/management/config").status_code == 200
    assert c.get("/management/audit").status_code == 200
    for path in ["/management/overview", "/finance/summary", "/hr/payroll", "/management/academics"]:
        assert c.get(path).status_code == 403, path
    assert c.get("/auth/me").json()["workspace"]["home"] == "/erp/management/approvals"


def test_payroll_view_is_audited() -> None:
    c = as_user("director", "DIR001")
    assert c.get("/hr/payroll").status_code == 200
    log = c.get("/management/audit?action=payroll.viewed").json()
    assert log["total"] >= 1
