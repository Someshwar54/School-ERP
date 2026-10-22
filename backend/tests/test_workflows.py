"""End-to-end API workflows: attendance, marks, publication, topics, complaints, leave, payments."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.models import AttendanceRecordHistory, MarkHistory
from tests.conftest import as_user, tenant_session


def _count(model) -> int:  # type: ignore[no-untyped-def]
    s = tenant_session("demo")
    try:
        return s.scalar(select(func.count()).select_from(model)) or 0
    finally:
        s.close()


def test_class_teacher_submits_missing_register_and_corrections_are_audited() -> None:
    c = as_user("staff", "EMP1004")  # class teacher of 9-B (seeded with a missing register)
    missing = c.get("/teacher/dashboard").json()["pending"]["missing_registers"]
    assert missing, "seed leaves one recent 9-B register missing"
    sec, day = missing[0]["section_id"], missing[0]["day"]
    register = c.get(f"/teacher/attendance?section_id={sec}&day={day}").json()
    assert register["submitted"] is False and register["students"]
    students = register["students"]

    partial = {"section_id": sec, "day": day, "records": [{"student_id": students[0]["student_id"], "status": "present"}]}
    assert c.put("/teacher/attendance", partial).json()["error"]["code"] == "incomplete_register"

    records = [{"student_id": s["student_id"], "status": "present"} for s in students]
    r = c.put("/teacher/attendance", {"section_id": sec, "day": day, "records": records})
    assert r.status_code == 200 and r.json()["action"] == "attendance.submitted"

    records[0]["status"] = "absent"
    no_reason = c.put("/teacher/attendance", {"section_id": sec, "day": day, "records": records})
    assert no_reason.json()["error"]["code"] == "reason_required"
    before = _count(AttendanceRecordHistory)
    fixed = c.put("/teacher/attendance", {"section_id": sec, "day": day, "records": records, "reason": "Marked wrongly"})
    assert fixed.json()["corrections"] == 1
    assert _count(AttendanceRecordHistory) == before + 1
    assert all(m["day"] != day for m in c.get("/teacher/dashboard").json()["pending"]["missing_registers"])


def test_attendance_rejects_future_and_non_instructional_days() -> None:
    c = as_user("staff", "EMP1001")
    sec = c.get("/auth/me").json()["workspace"]["class_teacher_of"][0]["section_id"]
    roster = c.get(f"/teacher/sections/{sec}/students").json()
    records = [{"student_id": s["student_id"], "status": "present"} for s in roster]
    future = (date.today() + timedelta(days=3)).isoformat()
    assert c.put("/teacher/attendance", {"section_id": sec, "day": future, "records": records}).status_code == 400
    r = c.put("/teacher/attendance", {"section_id": sec, "day": "2026-10-02", "records": records})  # Gandhi Jayanti
    assert r.status_code in (400, 403)  # holiday (or outside the correction window) — never recorded


def test_marks_entry_publication_and_corrections() -> None:
    teacher = as_user("staff", "EMP1001")
    a = next(x for x in teacher.get("/teacher/assignments").json() if x["section"] == "9-A")
    created = teacher.post(
        "/teacher/assessments",
        {
            "section_id": a["section_id"],
            "subject_id": a["subject_id"],
            "name": "Class Test (API)",
            "kind": "assignment",
            "max_marks": "20",
            "held_on": (date.today() - timedelta(days=1)).isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    aid = created.json()["id"]
    sheet = teacher.get(f"/teacher/assessments/{aid}/marks").json()["students"]

    too_high = teacher.put(
        f"/teacher/assessments/{aid}/marks", {"marks": [{"student_id": sheet[0]["student_id"], "marks_obtained": "21"}]}
    )
    assert too_high.json()["error"]["code"] == "exceeds_max"
    both = teacher.put(
        f"/teacher/assessments/{aid}/marks",
        {"marks": [{"student_id": sheet[0]["student_id"], "marks_obtained": "5", "is_absent": True}]},
    )
    assert both.status_code == 422

    coordinator = as_user("director", "DIR006")
    first_half = [{"student_id": s["student_id"], "marks_obtained": "15.5"} for s in sheet[:10]]
    teacher.put(f"/teacher/assessments/{aid}/marks", {"marks": first_half})
    incomplete = coordinator.post(f"/management/assessments/{aid}/publish")
    assert incomplete.status_code == 409 and incomplete.json()["error"]["code"] == "incomplete_marks"

    rest = [{"student_id": s["student_id"], "marks_obtained": "12"} for s in sheet[10:-1]] + [
        {"student_id": sheet[-1]["student_id"], "is_absent": True}
    ]
    teacher.put(f"/teacher/assessments/{aid}/marks", {"marks": rest})
    student_code = sheet[0]["student_code"]
    assert "Class Test (API)" not in str(as_user("student", student_code).get("/student/results").json())
    assert coordinator.post(f"/management/assessments/{aid}/publish").status_code == 200
    results = as_user("student", student_code).get("/student/results").json()
    row = next(s for e in results["exams"] if e["assessment"] == "Class Test (API)" for s in e["subjects"])
    assert row["marks_obtained"] == "15.50" and row["percent"] == 77.5

    correction = [{"student_id": sheet[0]["student_id"], "marks_obtained": "16"}]
    assert teacher.put(f"/teacher/assessments/{aid}/marks", {"marks": correction}).json()["error"]["code"] == "reason_required"
    before = _count(MarkHistory)
    ok = teacher.put(f"/teacher/assessments/{aid}/marks", {"marks": correction, "reason": "Re-totalled paper"})
    assert ok.json()["corrections"] == 1 and _count(MarkHistory) == before + 1


def test_topic_completion_requires_explicit_confirmation() -> None:
    c = as_user("staff", "EMP1001")
    a = next(x for x in c.get("/teacher/assignments").json() if x["section"] == "10-A")
    topics = c.get(f"/teacher/topics?section_id={a['section_id']}&subject_id={a['subject_id']}").json()["topics"]
    current = next(t for t in topics if t["status"] == "in_progress")

    dismissed = c.post(f"/teacher/topics/{current['id']}/action", {"action": "complete"})  # e.g. prompt closed
    assert dismissed.status_code == 400 and dismissed.json()["error"]["code"] == "confirmation_required"
    after = c.get(f"/teacher/topics?section_id={a['section_id']}&subject_id={a['subject_id']}").json()["topics"]
    assert next(t for t in after if t["id"] == current["id"])["status"] == "in_progress"

    planned = next(t for t in after if t["status"] in ("planned", "pending"))
    clash = c.post(f"/teacher/topics/{planned['id']}/action", {"action": "start"})
    assert clash.status_code == 409  # one topic in progress at a time

    done = c.post(f"/teacher/topics/{current['id']}/action", {"action": "complete", "confirm": True, "start_next": True})
    assert done.status_code == 200
    assert done.json()["topic"]["status"] == "completed" and done.json()["started_next"] is not None


def test_complaint_routing_respects_confidentiality() -> None:
    student = as_user("student", "STU0185")  # 9-A, class teacher EMP1001
    academic = student.post(
        "/student/complaints",
        {
            "category": "academic",
            "subject": "Need revision class",
            "description": "Please arrange a revision class before tests.",
        },
    )
    assert academic.json()["routed_to"] == "Class teacher"
    private = student.post(
        "/student/complaints",
        {
            "category": "academic",
            "subject": "Private academic issue",
            "description": "This is confidential and sensitive.",
            "is_confidential": True,
        },
    )
    assert private.json()["routed_to"] == "School management"
    teacher_view = {c["reference_no"] for c in as_user("staff", "EMP1001").get("/teacher/complaints").json()}
    assert academic.json()["reference_no"] in teacher_view
    assert private.json()["reference_no"] not in teacher_view


def test_leave_request_and_segregated_approval() -> None:
    staff = as_user("staff", "EMP2006")
    start = (date.today() + timedelta(days=30)).isoformat()
    leave = staff.post("/staff/leave", {"leave_type": "casual", "starts_on": start, "ends_on": start, "reason": "Family"})
    assert leave.status_code == 201
    overlap = staff.post("/staff/leave", {"leave_type": "sick", "starts_on": start, "ends_on": start, "reason": "Again"})
    assert overlap.status_code == 409
    assert (
        as_user("staff", "EMP2002")
        .post(f"/hr/leave-requests/{leave.json()['id']}/decision", {"decision": "approved"})
        .status_code
        == 403
    )
    hr_manager = as_user("director", "DIR005")
    assert hr_manager.post(f"/hr/leave-requests/{leave.json()['id']}/decision", {"decision": "approved"}).status_code == 200
    assert staff.get("/staff/leave").json()[0]["status"] == "approved"


def test_payment_recording_uses_exact_decimals_and_blocks_overpayment() -> None:
    finance = as_user("staff", "EMP2001")
    inv = finance.get("/finance/invoices?status=overdue&page_size=1").json()["items"][0]
    balance = Decimal(inv["balance"])
    over = finance.post(
        "/finance/payments",
        {
            "invoice_id": inv["id"],
            "amount": str(balance + Decimal("0.01")),
            "method": "cash",
            "paid_on": date.today().isoformat(),
        },
    )
    assert over.status_code == 409
    part = Decimal("1234.56")
    paid = finance.post(
        "/finance/payments", {"invoice_id": inv["id"], "amount": str(part), "method": "upi", "paid_on": date.today().isoformat()}
    )
    assert paid.status_code == 201
    assert Decimal(paid.json()["new_balance"]) == balance - part
    again = finance.get(f"/finance/invoices?q={inv['invoice_no']}").json()["items"][0]
    assert Decimal(again["balance"]) == balance - part
    assert (
        as_user("director", "DIR003")
        .post(
            "/finance/payments", {"invoice_id": inv["id"], "amount": "1", "method": "cash", "paid_on": date.today().isoformat()}
        )
        .status_code
        == 403
    )


def test_student_ledger_totals_are_consistent() -> None:
    fees = as_user("student", "STU0010").get("/student/fees").json()
    t = fees["totals"]
    assert Decimal(t["outstanding"]) == Decimal(t["billed"]) - Decimal(t["paid"]) + Decimal(t["refunded"])
    assert Decimal(t["billed"]) == sum(Decimal(i["net"]) for i in fees["invoices"])


def test_public_enquiry_validation_and_storage() -> None:
    from tests.conftest import ApiClient

    c = ApiClient()
    bad = c.http.post("/api/v1/public/enquiries", json={"parent_name": "A", "email": "x", "phone": "123", "grade_sought": ""})
    assert bad.status_code == 422
    ok = c.http.post(
        "/api/v1/public/enquiries",
        json={"parent_name": "Test Parent", "email": "parent@example.com", "phone": "9876500000", "grade_sought": "Grade 7"},
    )
    assert ok.status_code == 201 and "not connected" in ok.json()["notifications"]
    items = as_user("director", "DIR001").get("/management/enquiries").json()["items"]
    assert any(e["parent_name"] == "Test Parent" for e in items)


def test_config_update_is_validated_versioned_and_audited() -> None:
    admin = as_user("director", "DIR008")
    cfg = admin.get("/management/config").json()
    bad = admin.put(
        "/management/config", {"version": cfg["version"], "settings": {**cfg["settings"], "enabled_modules": ["hacking"]}}
    )
    assert bad.status_code == 422
    settings = {**cfg["settings"], "terminology": {**cfg["settings"]["terminology"], "section": "Division"}}
    ok = admin.put("/management/config", {"version": cfg["version"], "settings": settings})
    assert ok.status_code == 200
    stale = admin.put("/management/config", {"version": cfg["version"], "settings": settings})
    assert stale.status_code == 409
    assert (
        as_user("director", "DIR001")
        .put("/management/config", {"version": ok.json()["version"], "settings": settings})
        .status_code
        == 403
    )


def test_evaluation_cannot_be_finalised_without_complete_human_review() -> None:
    principal = as_user("director", "DIR002")
    ev = principal.get("/management/evaluations").json()
    draft = next(i for i in ev["items"] if i["status"] == "draft")
    r = principal.post(f"/management/evaluations/{draft['id']}/finalize", {"reviewer_comment": "Looks fine overall."})
    assert r.status_code == 400 and r.json()["error"]["code"] == "incomplete_scores"
    scores = {c["key"]: 3 for c in ev["rubric"]["criteria"]}
    assert principal.patch(f"/management/evaluations/{draft['id']}", {"scores": {"learning_progress": 9}}).status_code == 400
    assert principal.patch(f"/management/evaluations/{draft['id']}", {"scores": scores}).status_code == 200
    assert (
        principal.post(
            f"/management/evaluations/{draft['id']}/finalize", {"reviewer_comment": "Reviewed with evidence."}
        ).status_code
        == 200
    )
    assert as_user("director", "DIR003").get("/management/evaluations").status_code == 403
