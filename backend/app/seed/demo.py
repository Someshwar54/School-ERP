"""Idempotent seed of a fictional demo school for LOCAL DEVELOPMENT ONLY.

    python -m app.seed.demo            # full demo school (slug "demo")

Safe to run repeatedly: rows are matched on natural keys and never duplicated,
and existing passwords are never reset. Refuses to run when APP_ENV=production.
"""

import random
import sys
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import session_factory, set_tenant
from app.core.security import hash_password
from app.models import (
    AcademicYear,
    AdmissionEnquiry,
    Announcement,
    Assessment,
    AttendanceRecord,
    AttendanceSession,
    BellPeriod,
    CalendarDay,
    ClassTeacherAssignment,
    Complaint,
    ComplaintUpdate,
    Document,
    Enrollment,
    EvaluationRubric,
    Feedback,
    FeeHead,
    FeeStructure,
    Guardian,
    Invoice,
    InvoiceLine,
    LeaveRequest,
    LessonTopic,
    Mark,
    Message,
    MessageThread,
    Payment,
    PaymentAllocation,
    Permission,
    Refund,
    Role,
    RolePermission,
    School,
    SchoolClass,
    SchoolDomain,
    SchoolEvent,
    SchoolSettings,
    Section,
    StaffAttendance,
    StaffCompensation,
    StaffDuty,
    StaffProfile,
    StudentGuardian,
    StudentProfile,
    Subject,
    TeacherEvaluation,
    TeachingAssignment,
    Term,
    TimetableEntry,
    TopicFeedback,
    TopicProgressLog,
    User,
    UserRole,
)
from app.schemas.settings import SchoolSettingsModel
from app.seed import data
from app.services.rbac import PERMISSIONS, ROLE_TEMPLATES

D = Decimal


@dataclass
class SeedOptions:
    slug: str = "demo"
    name: str = "Sunrise Valley Public School"
    hosts: Sequence[str] = ("localhost", "127.0.0.1", "demo.school.local")
    grades: Sequence[int] = (6, 7, 8, 9, 10)
    sections_per_grade: int = 2
    students_per_section: int = 30
    full: bool = True  # False = minimal dataset (used for the second tenant in tests)
    today: date = field(default_factory=date.today)


def _chunks(rows: list[dict[str, Any]], size: int = 1000) -> Iterable[list[dict[str, Any]]]:
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def bulk_insert(db: Session, model: Any, rows: list[dict[str, Any]]) -> None:
    for chunk in _chunks(rows):
        db.execute(pg_insert(model).values(chunk).on_conflict_do_nothing())


def get_or_create(db: Session, model: Any, defaults: dict[str, Any] | None = None, **keys: Any) -> Any:
    obj = db.scalar(select(model).filter_by(**keys))
    if obj is None:
        obj = model(**keys, **(defaults or {}))
        db.add(obj)
        db.flush()
    return obj


def _empty(db: Session, model: Any) -> bool:
    return not db.scalar(select(func.count()).select_from(model))


def _hash_all(passwords: list[str]) -> list[str]:
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(hash_password, passwords))


class Seeder:
    def __init__(self, db: Session, opts: SeedOptions) -> None:
        self.db, self.o = db, opts
        self.rng = random.Random(f"{opts.slug}-2026")
        self.today = opts.today
        self.school: School
        self.sid: UUID

    # ---- foundation -------------------------------------------------------------------------------------------
    def run(self) -> School:
        db = self.db
        for code, (category, desc) in PERMISSIONS.items():
            db.execute(
                pg_insert(Permission)
                .values(code=code, category=category, description=desc)
                .on_conflict_do_update(index_elements=["code"], set_={"category": category, "description": desc})
            )
        self.school = get_or_create(db, School, defaults={"name": self.o.name}, slug=self.o.slug)
        self.sid = self.school.id
        for host in self.o.hosts:
            db.execute(pg_insert(SchoolDomain).values(id=uuid4(), school_id=self.sid, host=host).on_conflict_do_nothing())
        set_tenant(db, self.sid)
        if db.get(SchoolSettings, self.sid) is None:
            db.add(SchoolSettings(school_id=self.sid, settings=SchoolSettingsModel().model_dump()))
        self.roles = self._roles()
        self._calendar()
        self._structure()
        self._staff()
        self._students()
        self._assignments_and_timetable()
        if self.o.full:
            self._attendance()
            self._staff_attendance()
            self._assessments()
            self._topics()
            self._fees()
            self._engagement()
            self._operations()
        db.commit()
        return self.school

    def _roles(self) -> dict[str, UUID]:
        roles = {}
        for t in ROLE_TEMPLATES:
            role = get_or_create(
                self.db,
                Role,
                defaults={"name": t.name, "kind": t.kind, "description": t.description},
                school_id=self.sid,
                code=t.code,
            )
            roles[t.code] = role.id
            bulk_insert(
                self.db,
                RolePermission,
                [{"school_id": self.sid, "role_id": role.id, "permission_code": p} for p in t.permissions],
            )
        return roles

    def _calendar(self) -> None:
        t = self.today
        y = t.year if t.month >= 4 else t.year - 1
        self.year_start, self.year_end = date(y, 4, 1), date(y + 1, 3, 31)
        self.year = get_or_create(
            self.db,
            AcademicYear,
            defaults={"starts_on": self.year_start, "ends_on": self.year_end, "is_current": True},
            school_id=self.sid,
            name=f"{y}-{str(y + 1)[2:]}",
        )
        self.term1 = get_or_create(
            self.db,
            Term,
            defaults={"starts_on": date(y, 4, 1), "ends_on": date(y, 9, 30)},
            school_id=self.sid,
            academic_year_id=self.year.id,
            name="Term 1",
        )
        self.term2 = get_or_create(
            self.db,
            Term,
            defaults={"starts_on": date(y, 10, 1), "ends_on": date(y + 1, 3, 31)},
            school_id=self.sid,
            academic_year_id=self.year.id,
            name="Term 2",
        )
        days: list[tuple[date, str, str]] = [
            (date(y, 8, 15), "holiday", "Independence Day"),
            (date(y, 10, 2), "holiday", "Gandhi Jayanti"),
            (date(y, 10, 20), "holiday", "Dussehra"),
            (date(y + 1, 1, 26), "holiday", "Republic Day"),
            (date(y, 9, 5), "non_instructional", "Teachers' Day celebrations"),
        ]
        d = date(y, 5, 15)
        while d <= date(y, 6, 30):
            days.append((d, "non_instructional", "Summer vacation"))
            d += timedelta(days=1)
        for offset in range(5):
            days.append((date(y, 11, 7) + timedelta(days=offset), "holiday", "Diwali break"))
        for month in range(4, 16):
            first = date(y + (month - 1) // 12, (month - 1) % 12 + 1, 1)
            second_sat = first + timedelta(days=(5 - first.weekday()) % 7 + 7)
            days.append((second_sat, "non_instructional", "Second Saturday"))
        bulk_insert(
            self.db, CalendarDay, [{"id": uuid4(), "school_id": self.sid, "day": dd, "kind": k, "name": n} for dd, k, n in days]
        )
        bells = [
            (1, "08:00", "08:40"),
            (2, "08:40", "09:20"),
            (3, "09:20", "10:00"),
            (4, "10:20", "11:00"),
            (5, "11:00", "11:40"),
            (6, "12:20", "13:00"),
            (7, "13:00", "13:40"),
        ]
        bulk_insert(
            self.db,
            BellPeriod,
            [
                {
                    "id": uuid4(),
                    "school_id": self.sid,
                    "period_no": n,
                    "label": f"Period {n}",
                    "starts_at": time.fromisoformat(a),
                    "ends_at": time.fromisoformat(b),
                }
                for n, a, b in bells
            ],
        )
        self.db.flush()
        closed = set(self.db.scalars(select(CalendarDay.day)))
        end = min(self.today - timedelta(days=1), self.year_end)
        start = max(self.year_start, self.today - timedelta(days=120))
        self.school_days = [
            start + timedelta(days=i)
            for i in range((end - start).days + 1)
            if (start + timedelta(days=i)).weekday() != 6 and (start + timedelta(days=i)) not in closed
        ]

    def _structure(self) -> None:
        self.subjects = {
            code: get_or_create(self.db, Subject, defaults={"name": name}, school_id=self.sid, code=code).id
            for code, name in data.SUBJECTS
        }
        self.sections: list[Section] = []
        self.section_grade: dict[UUID, int] = {}
        self.class_ids: dict[int, UUID] = {}
        for g in self.o.grades:
            cls = get_or_create(self.db, SchoolClass, defaults={"name": f"Grade {g}"}, school_id=self.sid, grade_number=g)
            self.class_ids[g] = cls.id
            for letter in "ABCD"[: self.o.sections_per_grade]:
                sec = get_or_create(
                    self.db,
                    Section,
                    defaults={"room": f"{g}{letter}-101"},
                    school_id=self.sid,
                    academic_year_id=self.year.id,
                    class_id=cls.id,
                    name=letter,
                )
                self.sections.append(sec)
                self.section_grade[sec.id] = g

    # ---- people -----------------------------------------------------------------------------------------------
    def _users(self, specs: list[dict[str, Any]]) -> dict[str, UUID]:
        """specs: login_id, account_type, display_name, password, roles. Never resets an existing password."""
        existing = dict(self.db.execute(select(User.login_id, User.id)).all())
        new = [s for s in specs if s["login_id"] not in existing]
        hashes = _hash_all([s["password"] for s in new])
        for s, h in zip(new, hashes, strict=True):
            uid = uuid4()
            self.db.add(
                User(
                    id=uid,
                    school_id=self.sid,
                    login_id=s["login_id"],
                    account_type=s["account_type"],
                    display_name=s["display_name"],
                    password_hash=h,
                    must_change_password=True,
                )
            )
            existing[s["login_id"]] = uid
        self.db.flush()
        bulk_insert(
            self.db,
            UserRole,
            [
                {"school_id": self.sid, "user_id": existing[s["login_id"]], "role_id": self.roles[r]}
                for s in specs
                for r in s["roles"]
            ],
        )
        return existing

    def _staff(self) -> None:
        teachers = data.TEACHERS if self.o.full else data.TEACHERS[:2]
        specs: list[dict[str, Any]] = []
        profiles: list[dict[str, Any]] = []
        for code, first, last, subj, _g, _ct in teachers:
            specs.append(
                {
                    "login_id": code,
                    "account_type": "staff",
                    "display_name": f"{first} {last}",
                    "password": f"Staff@{code[-4:]}",
                    "roles": ["teacher"],
                }
            )
            profiles.append(
                {
                    "staff_code": code,
                    "first_name": first,
                    "last_name": last,
                    "staff_type": "teaching",
                    "designation": "Teacher",
                    "department": dict(data.SUBJECTS)[subj],
                    "qualification": "M.Sc., B.Ed." if subj in ("MAT", "SCI") else "M.A., B.Ed.",
                    "is_public": True,
                    "public_bio": f"Teaches {dict(data.SUBJECTS)[subj]}.",
                }
            )
        for code, first, last, desig, dept, roles in data.NON_TEACHING if self.o.full else data.NON_TEACHING[:1]:
            specs.append(
                {
                    "login_id": code,
                    "account_type": "staff",
                    "display_name": f"{first} {last}",
                    "password": f"Staff@{code[-4:]}",
                    "roles": list(roles),
                }
            )
            profiles.append(
                {
                    "staff_code": code,
                    "first_name": first,
                    "last_name": last,
                    "staff_type": "non_teaching",
                    "designation": desig,
                    "department": dept,
                    "is_public": False,
                }
            )
        management: list[tuple[str, str, str, str, tuple[str, ...]]] = list(
            data.MANAGEMENT if self.o.full else data.MANAGEMENT[:1]
        )
        for code, first, last, desig, mgmt_roles in management:
            specs.append(
                {
                    "login_id": code,
                    "account_type": "management",
                    "display_name": f"{first} {last}",
                    "password": f"Mgmt@{code}",
                    "roles": list(mgmt_roles),
                }
            )
            profiles.append(
                {
                    "staff_code": code,
                    "first_name": first,
                    "last_name": last,
                    "staff_type": "management",
                    "designation": desig,
                    "department": "Management",
                    "is_public": desig in ("Director", "Principal"),
                }
            )
        users = self._users(specs)
        self.user_ids = users
        rows = []
        for p in profiles:
            rows.append(
                {
                    "id": uuid4(),
                    "school_id": self.sid,
                    "user_id": users[p["staff_code"]],
                    "joining_date": date(2015 + self.rng.randint(0, 9), self.rng.randint(1, 12), 1),
                    "email": f"{p['first_name'].lower()}.{p['last_name'].lower()}@{self.o.slug}.school.example",
                    "phone": None,
                    "qualification": p.get("qualification"),
                    "public_bio": p.get("public_bio"),
                    **{k: v for k, v in p.items() if k not in ("qualification", "public_bio")},
                }
            )
        bulk_insert(self.db, StaffProfile, rows)
        self.staff = dict(self.db.execute(select(StaffProfile.staff_code, StaffProfile.id)).all())
        if self.o.full:
            comp = []
            for code, sid in self.staff.items():
                base = 52000 if code.startswith("EMP1") else 34000 if code.startswith("EMP2") else 120000
                comp.append(
                    {
                        "id": uuid4(),
                        "school_id": self.sid,
                        "staff_id": sid,
                        "effective_from": self.year_start,
                        "pay_grade": "T2" if code.startswith("EMP1") else "N1" if code.startswith("EMP2") else "M1",
                        "monthly_gross": D(base + self.rng.randint(0, 40) * 500),
                        "bank_account_last4": f"{self.rng.randint(0, 9999):04d}",
                    }
                )
            bulk_insert(self.db, StaffCompensation, comp)

    def _students(self) -> None:
        rng = self.rng
        specs, profiles, n = [], [], 0
        used_phones: set[str] = set()
        for sec in self.sections:
            g = self.section_grade[sec.id]
            for roll in range(1, self.o.students_per_section + 1):
                n += 1
                female = rng.random() < 0.5
                first = rng.choice(data.FIRST_NAMES_F if female else data.FIRST_NAMES_M)
                last = rng.choice(data.LAST_NAMES)
                phone = f"9{rng.randint(100000000, 999999999)}"
                while phone in used_phones:
                    phone = f"9{rng.randint(100000000, 999999999)}"
                used_phones.add(phone)
                code = f"STU{n:04d}"
                # Prototype convention: the initial password is the registered phone number (see README).
                specs.append(
                    {
                        "login_id": code,
                        "account_type": "student",
                        "display_name": f"{first} {last}",
                        "password": phone,
                        "roles": [],
                    }
                )
                profiles.append((code, first, last, female, phone, g, sec.id, roll))
        users = self._users(specs)
        rows = []
        for code, first, last, female, phone, g, _sec, _roll in profiles:
            dob = date(self.year_start.year - g - 6, rng.randint(1, 12), rng.randint(1, 28))
            rows.append(
                {
                    "id": uuid4(),
                    "school_id": self.sid,
                    "user_id": users[code],
                    "student_code": code,
                    "admission_no": f"ADM-{code[3:]}",
                    "first_name": first,
                    "last_name": last,
                    "date_of_birth": dob,
                    "gender": "female" if female else "male",
                    "admission_date": date(self.year_start.year - rng.randint(0, g - 5), 4, 1),
                    "phone": phone,
                    "email": None,
                    "address": f"{rng.randint(1, 200)}, Fictional Nagar, Demo City",
                    "blood_group": rng.choice(["A+", "B+", "O+", "AB+", "O-", None]),
                }
            )
        bulk_insert(self.db, StudentProfile, rows)
        self.students = dict(self.db.execute(select(StudentProfile.student_code, StudentProfile.id)).all())
        bulk_insert(
            self.db,
            Enrollment,
            [
                {
                    "id": uuid4(),
                    "school_id": self.sid,
                    "student_id": self.students[code],
                    "section_id": sec,
                    "academic_year_id": self.year.id,
                    "roll_no": roll,
                    "status": "active",
                }
                for code, *_rest, sec, roll in profiles
            ],
        )
        self.roster: dict[UUID, list[UUID]] = {}
        for code, *_rest, sec_id, _roll in profiles:
            self.roster.setdefault(sec_id, []).append(self.students[code])
        # Guardians: profile + verified relationship (guardian logins are not activated in this prototype).
        if _empty(self.db, Guardian):
            verifier = self.user_ids.get("DIR002") or next(iter(self.user_ids.values()))
            gs, links = [], []
            for code, _first, last, _f, phone, *_ in profiles:
                gid = uuid4()
                gs.append(
                    {
                        "id": gid,
                        "school_id": self.sid,
                        "full_name": f"{rng.choice(data.FIRST_NAMES_M)} {last}",
                        "phone": phone,
                        "email": None,
                        "occupation": rng.choice(["Engineer", "Teacher", "Business", "Doctor", None]),
                    }
                )
                links.append(
                    {
                        "id": uuid4(),
                        "school_id": self.sid,
                        "student_id": self.students[code],
                        "guardian_id": gid,
                        "relationship": "father",
                        "is_primary": True,
                        "verification_status": "verified",
                        "verified_at": datetime.now(UTC),
                        "verified_by_user_id": verifier,
                    }
                )
            bulk_insert(self.db, Guardian, gs)
            bulk_insert(self.db, StudentGuardian, links)

    def _assignments_and_timetable(self) -> None:
        order = [c for c, _ in data.SUBJECTS]  # 7 subjects -> 7 periods; rotation avoids teacher clashes
        half = len(self.sections) // 2 or 1
        teachers = data.TEACHERS if self.o.full else data.TEACHERS[:2]
        by_subject_group = {(subj, g): code for code, _f, _l, subj, g, _ct in teachers}
        ta, ct, tt = [], [], []
        for i, sec in enumerate(self.sections):
            group = 0 if i < half else 1
            for subj in order:
                code = by_subject_group.get((subj, group)) or by_subject_group.get((subj, 0))
                if code is None and not self.o.full:
                    code = teachers[0][0] if subj != "SCI" else teachers[1][0]
                if code is None:
                    continue
                ta.append(
                    {
                        "id": uuid4(),
                        "school_id": self.sid,
                        "academic_year_id": self.year.id,
                        "staff_id": self.staff[code],
                        "section_id": sec.id,
                        "subject_id": self.subjects[subj],
                    }
                )
            for day in range(6):
                for period in range(1, 8):
                    subj = order[(day + period + i) % 7]
                    code = by_subject_group.get((subj, group))
                    tt.append(
                        {
                            "id": uuid4(),
                            "school_id": self.sid,
                            "academic_year_id": self.year.id,
                            "section_id": sec.id,
                            "subject_id": self.subjects[subj],
                            "staff_id": self.staff[code] if code and self.o.full else None,
                            "day_of_week": day,
                            "period_no": period,
                            "room": "Playground" if subj == "PED" else "Computer Lab" if subj == "CSC" else sec.room,
                        }
                    )
        for code, *_x, ct_idx in teachers:
            if ct_idx is not None and ct_idx < len(self.sections):
                ct.append(
                    {
                        "id": uuid4(),
                        "school_id": self.sid,
                        "academic_year_id": self.year.id,
                        "section_id": self.sections[ct_idx].id,
                        "staff_id": self.staff[code],
                    }
                )
        if not self.o.full:
            ct = [
                {
                    "id": uuid4(),
                    "school_id": self.sid,
                    "academic_year_id": self.year.id,
                    "section_id": self.sections[0].id,
                    "staff_id": self.staff[teachers[0][0]],
                }
            ]
        bulk_insert(self.db, TeachingAssignment, ta)
        bulk_insert(self.db, ClassTeacherAssignment, ct)
        bulk_insert(self.db, TimetableEntry, tt)
        self.db.flush()
        self.assign = {(r.section_id, r.subject_id): r.staff_id for r in self.db.scalars(select(TeachingAssignment))}
        self.class_teacher = {r.section_id: r.staff_id for r in self.db.scalars(select(ClassTeacherAssignment))}
        self.staff_user = dict(self.db.execute(select(StaffProfile.id, StaffProfile.user_id)).all())

    # ---- records ----------------------------------------------------------------------------------------------
    def _attendance(self) -> None:
        if not _empty(self.db, AttendanceSession):
            return
        rng = self.rng
        propensity = {
            s: (rng.uniform(0.62, 0.74) if rng.random() < 0.06 else rng.uniform(0.86, 0.99))
            for ids in self.roster.values()
            for s in ids
        }
        recent = self.school_days[-3:] if len(self.school_days) >= 3 else self.school_days
        skip = set()
        if len(self.sections) >= 8 and recent:
            skip = {(self.sections[7].id, recent[-1]), (self.sections[2].id, recent[0])}  # deliberate gaps
        sessions, records = [], []
        for sec in self.sections:
            taker = self.staff_user[self.class_teacher[sec.id]]
            for day in self.school_days:
                if (sec.id, day) in skip:
                    continue
                sess_id = uuid4()
                stamp = datetime.combine(day, time(3, 0), tzinfo=UTC)
                sessions.append(
                    {
                        "id": sess_id,
                        "school_id": self.sid,
                        "section_id": sec.id,
                        "day": day,
                        "kind": "daily",
                        "period_no": 0,
                        "taken_by_user_id": taker,
                        "submitted_at": stamp,
                    }
                )
                for st in self.roster[sec.id]:
                    r = rng.random()
                    p = propensity[st]
                    status = (
                        "present"
                        if r < p - 0.03
                        else "late"
                        if r < p
                        else "approved_leave"
                        if r < p + (1 - p) * 0.3
                        else "excused"
                        if r < p + (1 - p) * 0.4
                        else "absent"
                    )
                    records.append(
                        {
                            "id": uuid4(),
                            "school_id": self.sid,
                            "session_id": sess_id,
                            "student_id": st,
                            "status": status,
                            "updated_by_user_id": taker,
                        }
                    )
        bulk_insert(self.db, AttendanceSession, sessions)
        bulk_insert(self.db, AttendanceRecord, records)

    def _staff_attendance(self) -> None:
        if not _empty(self.db, StaffAttendance):
            return
        rows = []
        for sid in self.staff.values():
            for day in self.school_days:
                r = self.rng.random()
                status = "present" if r < 0.93 else "late" if r < 0.96 else "on_leave" if r < 0.985 else "absent"
                rows.append(
                    {
                        "id": uuid4(),
                        "school_id": self.sid,
                        "staff_id": sid,
                        "day": day,
                        "status": status,
                        "check_in": time(7, 40 + self.rng.randint(0, 15)) if status in ("present", "late") else None,
                        "check_out": time(15, self.rng.randint(0, 50)) if status in ("present", "late") else None,
                    }
                )
        bulk_insert(self.db, StaffAttendance, rows)

    def _assessments(self) -> None:
        y = self.year_start.year
        plan = [
            ("Unit Test 1", "unit_test", D(25), date(y, 7, 15), self.term1, True),
            ("Unit Test 2", "unit_test", D(25), date(y, 8, 20), self.term1, True),
            ("Half-Yearly Examination", "half_yearly", D(80), date(y, 9, 22), self.term1, True),
            ("Unit Test 3", "unit_test", D(25), date(y, 10, 15), self.term2, False),
        ]
        plan = [p for p in plan if p[3] < self.today]
        publisher = self.user_ids.get("DIR006")
        rows = []
        for sec in self.sections:
            for subj in data.ASSESSED_SUBJECTS:
                staff = self.assign.get((sec.id, self.subjects[subj]))
                for name, kind, mx, held, term, published in plan:
                    rows.append(
                        {
                            "id": uuid4(),
                            "school_id": self.sid,
                            "academic_year_id": self.year.id,
                            "term_id": term.id,
                            "section_id": sec.id,
                            "subject_id": self.subjects[subj],
                            "name": name,
                            "kind": kind,
                            "max_marks": mx,
                            "held_on": held,
                            "created_by_user_id": self.staff_user.get(staff) if staff else None,
                            "is_published": published,
                            "published_at": datetime.combine(held + timedelta(days=10), time(6), tzinfo=UTC)
                            if published
                            else None,
                            "published_by_user_id": publisher if published else None,
                        }
                    )
        bulk_insert(self.db, Assessment, rows)
        if not _empty(self.db, Mark):
            return
        rng = self.rng
        ability = {s: min(0.97, max(0.25, rng.gauss(0.68, 0.14))) for ids in self.roster.values() for s in ids}
        offsets = {(s, subj): rng.gauss(0, 0.07) for s in ability for subj in self.subjects.values()}
        marks = []
        for a in self.db.scalars(select(Assessment)):
            # Leave the unpublished test incomplete for some sections to demonstrate "missing marks".
            if not a.is_published and self.sections.index(next(s for s in self.sections if s.id == a.section_id)) % 3 == 0:
                continue
            staff = self.assign.get((a.section_id, a.subject_id))
            for st in self.roster[a.section_id]:
                absent = rng.random() < 0.02
                score = (
                    None
                    if absent
                    else max(
                        D(0),
                        min(
                            a.max_marks,
                            D(
                                round(float(a.max_marks) * (ability[st] + offsets[(st, a.subject_id)] + rng.gauss(0, 0.06)) * 2)
                                / 2
                            ),
                        ),
                    )
                )
                marks.append(
                    {
                        "id": uuid4(),
                        "school_id": self.sid,
                        "assessment_id": a.id,
                        "student_id": st,
                        "marks_obtained": score,
                        "is_absent": absent,
                        "entered_by_user_id": self.staff_user.get(staff) if staff else None,
                        "updated_at": datetime.combine(a.held_on + timedelta(days=4), time(9), tzinfo=UTC),
                    }
                )
        bulk_insert(self.db, Mark, marks)

    def _topics(self) -> None:
        if not _empty(self.db, LessonTopic):
            return
        rng = self.rng
        progress_ratio = min(1.0, max(0.0, (self.today - self.year_start).days / 330))
        topics, logs = [], []
        for sec in self.sections:
            for subj in data.ASSESSED_SUBJECTS:
                actor = self.staff_user[self.assign[(sec.id, self.subjects[subj])]]
                done = max(0, min(9, round(10 * progress_ratio + rng.choice([-1, 0, 0, 1]))))
                for seq, title in enumerate(data.TOPICS[subj], start=1):
                    tid = uuid4()
                    status = "completed" if seq <= done else "in_progress" if seq == done + 1 else "planned"
                    if status == "planned" and seq == done + 2 and rng.random() < 0.25:
                        status = "pending"
                    started = self.year_start + timedelta(days=75 + seq * 14) if status != "planned" else None
                    completed = started + timedelta(days=12) if status == "completed" and started else None
                    topics.append(
                        {
                            "id": tid,
                            "school_id": self.sid,
                            "academic_year_id": self.year.id,
                            "section_id": sec.id,
                            "subject_id": self.subjects[subj],
                            "sequence": seq,
                            "title": title,
                            "planned_periods": rng.choice([4, 5, 6, 8]),
                            "periods_used": rng.randint(3, 7) if status in ("completed", "in_progress") else 0,
                            "status": status,
                            "started_on": started,
                            "completed_on": completed,
                            "completed_by_user_id": actor if completed else None,
                        }
                    )
                    if started and started < self.today:
                        logs.append(
                            {
                                "id": uuid4(),
                                "school_id": self.sid,
                                "topic_id": tid,
                                "action": "started",
                                "occurred_on": started,
                                "actor_user_id": actor,
                            }
                        )
                    if completed and completed < self.today:
                        logs.append(
                            {
                                "id": uuid4(),
                                "school_id": self.sid,
                                "topic_id": tid,
                                "action": "completed",
                                "occurred_on": completed,
                                "actor_user_id": actor,
                            }
                        )
        bulk_insert(self.db, LessonTopic, topics)
        bulk_insert(self.db, TopicProgressLog, logs)
        # Topic feedback from one demo section (9-A) for its Mathematics topics.
        sec = self.sections[6]
        fb = []
        for t in self.db.scalars(
            select(LessonTopic).where(LessonTopic.section_id == sec.id, LessonTopic.status.in_(("completed", "in_progress")))
        ):
            for st in self.roster[sec.id][: rng.randint(6, 14)]:
                fb.append(
                    {
                        "id": uuid4(),
                        "school_id": self.sid,
                        "topic_id": t.id,
                        "student_id": st,
                        "understanding": rng.choice([2, 3, 3, 4, 4, 4, 5, 5]),
                        "comment": rng.choice(
                            [None, None, "Need more practice problems.", "Clear explanation.", "Please revise the last part."]
                        ),
                        "share_name": rng.random() < 0.8,
                    }
                )
        bulk_insert(self.db, TopicFeedback, fb)

    def _fees(self) -> None:
        heads = {
            c: get_or_create(self.db, FeeHead, defaults={"name": n}, school_id=self.sid, code=c).id for c, n in data.FEE_HEADS
        }
        structure = []
        for g, cid in self.class_ids.items():
            for term in (self.term1, self.term2):
                for code, base_amount in (
                    ("TUITION", 15000 + 1000 * (g - 6)),
                    ("DEVELOPMENT", 3000),
                    ("EXAM", 1000),
                    ("ACTIVITY", 1500),
                    ("TRANSPORT", 6000),
                ):
                    structure.append(
                        {
                            "id": uuid4(),
                            "school_id": self.sid,
                            "academic_year_id": self.year.id,
                            "class_id": cid,
                            "fee_head_id": heads[code],
                            "term_id": term.id,
                            "amount": D(base_amount),
                        }
                    )
        bulk_insert(self.db, FeeStructure, structure)
        if not _empty(self.db, Invoice):
            return
        rng = self.rng
        fee = {(r.class_id, r.term_id, r.fee_head_id): r.amount for r in self.db.scalars(select(FeeStructure))}
        receiver = self.user_ids.get("EMP2001")
        y = self.year_start.year
        invoices, lines, payments, allocs, refunds = [], [], [], [], []
        inv_n = rcpt_n = 0
        refund_done = False
        for sec in self.sections:
            cid = self.class_ids[self.section_grade[sec.id]]
            for st in self.roster[sec.id]:
                transport = rng.random() < 0.4
                sibling = rng.random() < 0.08
                merit = rng.random() < 0.02
                for term, issued, due, pay_profile in (
                    (self.term1, date(y, 4, 5), date(y, 4, 30), (0.92, 0.05)),
                    (self.term2, date(y, 10, 1), date(y, 10, 31), (0.45, 0.10)),
                ):
                    if issued > self.today:
                        continue
                    inv_n += 1
                    iid = uuid4()
                    invoices.append(
                        {
                            "id": iid,
                            "school_id": self.sid,
                            "student_id": st,
                            "academic_year_id": self.year.id,
                            "term_id": term.id,
                            "invoice_no": f"INV-{y}-{inv_n:05d}",
                            "issued_on": issued,
                            "due_on": due,
                            "status": "issued",
                        }
                    )
                    total: Decimal = D(0)
                    for code in ("TUITION", "DEVELOPMENT", "EXAM", "ACTIVITY") + (("TRANSPORT",) if transport else ()):
                        amt = fee[(cid, term.id, heads[code])]
                        total += amt
                        lines.append(
                            {
                                "id": uuid4(),
                                "school_id": self.sid,
                                "invoice_id": iid,
                                "fee_head_id": heads[code],
                                "line_type": "charge",
                                "description": dict(data.FEE_HEADS)[code],
                                "amount": amt,
                            }
                        )
                    if sibling:
                        amt = (fee[(cid, term.id, heads["TUITION"])] * D("0.10")).quantize(D("0.01"))
                        total -= amt
                        lines.append(
                            {
                                "id": uuid4(),
                                "school_id": self.sid,
                                "invoice_id": iid,
                                "fee_head_id": heads["TUITION"],
                                "line_type": "concession",
                                "description": "Sibling concession (10% of tuition)",
                                "amount": amt,
                            }
                        )
                    if merit:
                        total -= D(5000)
                        lines.append(
                            {
                                "id": uuid4(),
                                "school_id": self.sid,
                                "invoice_id": iid,
                                "fee_head_id": None,
                                "line_type": "concession",
                                "description": "Merit scholarship",
                                "amount": D(5000),
                            }
                        )
                    r = rng.random()
                    paid = total if r < pay_profile[0] else (total * D("0.5")).quantize(D("1")) if r < sum(pay_profile) else D(0)
                    paid_on = min(self.today - timedelta(days=1), due - timedelta(days=rng.randint(0, 20)))
                    if paid > 0 and paid_on >= issued:
                        rcpt_n += 1
                        pid = uuid4()
                        overpay = D(500) if not refund_done and paid == total else D(0)
                        payments.append(
                            {
                                "id": pid,
                                "school_id": self.sid,
                                "student_id": st,
                                "receipt_no": f"RCPT-{y}-{rcpt_n:05d}",
                                "amount": paid + overpay,
                                "paid_on": paid_on,
                                "method": rng.choice(["upi", "upi", "bank_transfer", "cash", "card"]),
                                "reference": f"TXN{rng.randint(10**8, 10**9)}",
                                "received_by_user_id": receiver,
                            }
                        )
                        allocs.append(
                            {"id": uuid4(), "school_id": self.sid, "payment_id": pid, "invoice_id": iid, "amount": paid}
                        )
                        if overpay:
                            refund_done = True
                            refunds.append(
                                {
                                    "id": uuid4(),
                                    "school_id": self.sid,
                                    "payment_id": pid,
                                    "amount": overpay,
                                    "refunded_on": paid_on + timedelta(days=7),
                                    "reason": "Excess amount paid; refunded",
                                    "approved_by_user_id": self.user_ids.get("DIR004") or receiver,
                                }
                            )
        for model, rows in (
            (Invoice, invoices),
            (InvoiceLine, lines),
            (Payment, payments),
            (PaymentAllocation, allocs),
            (Refund, refunds),
        ):
            bulk_insert(self.db, model, rows)

    def _engagement(self) -> None:
        now = datetime.now(UTC)
        author = self.user_ids["DIR002"]
        sec9a = self.sections[6]
        if _empty(self.db, Announcement):
            for title, body, aud, sec, pinned, days in [
                (
                    "Half-yearly results published",
                    "Results for the Half-Yearly Examination are now available in the ERP.",
                    "students",
                    None,
                    True,
                    20,
                ),
                (
                    "Parent-teacher meeting on Saturday",
                    "PTM for all grades will be held in the main block from 9:00 to 12:30.",
                    "all",
                    None,
                    False,
                    4,
                ),
                (
                    "Staff meeting: Term 2 planning",
                    "All teaching staff to assemble in the conference room at 2:00 pm on Friday.",
                    "staff",
                    None,
                    False,
                    2,
                ),
                (
                    "Grade 9-A: Science lab schedule",
                    "Science practicals for 9-A move to Thursday period 5 this month.",
                    "students",
                    sec9a.id,
                    False,
                    1,
                ),
                (
                    "Board review: Q2 operations",
                    "Quarterly operational review pack is ready for management.",
                    "management",
                    None,
                    False,
                    3,
                ),
                (
                    "Annual sports day registrations open",
                    "Register with your PE teacher by the end of the month.",
                    "all",
                    None,
                    False,
                    6,
                ),
            ]:
                self.db.add(
                    Announcement(
                        school_id=self.sid,
                        title=title,
                        body=body,
                        audience=aud,
                        section_id=sec,
                        is_pinned=pinned,
                        published_at=now - timedelta(days=days),
                        created_by_user_id=author,
                    )
                )
        if _empty(self.db, SchoolEvent):
            base = datetime.combine(self.today, time(4, 0), tzinfo=UTC)
            for title, desc, offset, loc, aud in [
                ("Annual Sports Day", "Track and field events for all grades.", 18, "School grounds", "all"),
                ("Science Exhibition", "Student projects from grades 6-10.", 30, "Main hall", "all"),
                ("Parent-Teacher Meeting", "Term 2 progress discussions.", 3, "Classrooms", "all"),
                ("Staff professional development workshop", "Formative assessment practices.", 9, "Conference room", "staff"),
                ("Inter-house debate (completed)", "Topic: Technology in classrooms.", -12, "Auditorium", "all"),
            ]:
                self.db.add(
                    SchoolEvent(
                        school_id=self.sid,
                        title=title,
                        description=desc,
                        starts_at=base + timedelta(days=offset),
                        ends_at=base + timedelta(days=offset, hours=4),
                        location=loc,
                        audience=aud,
                    )
                )
        if _empty(self.db, Complaint):
            students = self.roster[sec9a.id]
            stu_user = dict(self.db.execute(select(StudentProfile.id, StudentProfile.user_id)).all())
            items = [
                (
                    students[0],
                    "academic",
                    "Need extra help with algebra",
                    "Could we have a doubt-clearing session?",
                    False,
                    "in_review",
                    True,
                ),
                (
                    students[1],
                    "facilities",
                    "Water cooler not working",
                    "The cooler on floor 2 has not worked for a week.",
                    False,
                    "open",
                    False,
                ),
                (
                    students[2],
                    "transport",
                    "Bus route 4 often late",
                    "The bus reaches 15 minutes late most days.",
                    False,
                    "resolved",
                    False,
                ),
                (
                    students[3],
                    "conduct",
                    "Concern about behaviour in class",
                    "Confidential matter regarding another student.",
                    True,
                    "open",
                    False,
                ),
                (
                    students[4],
                    "academic",
                    "Homework load before tests",
                    "Too many assignments in the same week.",
                    False,
                    "open",
                    True,
                ),
                (
                    self.roster[self.sections[0].id][0],
                    "other",
                    "Personal concern",
                    "I would like to speak to the counsellor privately.",
                    True,
                    "in_review",
                    False,
                ),
            ]
            for n, (st, cat, subj, desc, conf, status, assign_ct) in enumerate(items, start=1):
                sec_id = next(s for s, ids in self.roster.items() if st in ids)
                c = Complaint(
                    school_id=self.sid,
                    reference_no=f"CMP-{self.year_start.year}-{n:04d}",
                    raised_by_user_id=stu_user[st],
                    student_id=st,
                    section_id=sec_id,
                    category=cat,
                    subject=subj,
                    description=desc,
                    is_confidential=conf,
                    status=status,
                    assigned_staff_id=self.class_teacher[sec_id] if assign_ct and not conf else None,
                    resolved_at=now - timedelta(days=2) if status == "resolved" else None,
                )
                self.db.add(c)
                self.db.flush()
                if status != "open":
                    self.db.add(
                        ComplaintUpdate(
                            school_id=self.sid,
                            complaint_id=c.id,
                            author_user_id=author,
                            note="Acknowledged and under review."
                            if status == "in_review"
                            else "Transport vendor informed; timing fixed.",
                            new_status=status,
                        )
                    )
        if _empty(self.db, Feedback):
            stu_users = list(self.db.scalars(select(User.id).where(User.account_type == "student").limit(60)))
            cats = ["teaching", "facilities", "transport", "communication", "general"]
            for i, uid in enumerate(stu_users):
                anon = i % 4 == 0
                self.db.add(
                    Feedback(
                        school_id=self.sid,
                        submitted_by_user_id=None if anon else uid,
                        account_type="student",
                        category=cats[i % 5],
                        rating=self.rng.choice([3, 4, 4, 5, 5, 2]),
                        is_anonymous=anon,
                        comment=self.rng.choice(
                            [None, "Good overall.", "Library hours could be longer.", "Teachers are helpful."]
                        ),
                    )
                )
        if _empty(self.db, MessageThread):
            teacher = self.class_teacher[sec9a.id]
            stu_user = dict(self.db.execute(select(StudentProfile.id, StudentProfile.user_id)).all())
            for st, subject, q, a in [
                (
                    self.roster[sec9a.id][0],
                    "Doubt in linear equations",
                    "Ma'am, I did not understand question 4 of exercise 3.2.",
                    "Let's go over it in the doubt session on Thursday.",
                ),
                (self.roster[sec9a.id][1], "Missed class on Monday", "I was absent on Monday. What was covered?", None),
            ]:
                th = MessageThread(
                    school_id=self.sid,
                    student_id=st,
                    staff_id=teacher,
                    subject=subject,
                    created_by_user_id=stu_user[st],
                    last_message_at=now - timedelta(hours=5),
                )
                self.db.add(th)
                self.db.flush()
                self.db.add(Message(school_id=self.sid, thread_id=th.id, sender_user_id=stu_user[st], body=q))
                if a:
                    self.db.add(Message(school_id=self.sid, thread_id=th.id, sender_user_id=self.staff_user[teacher], body=a))

    def _operations(self) -> None:
        if _empty(self.db, LeaveRequest):
            for code, lt, start, days, reason, status in [
                ("EMP1002", "casual", 5, 1, "Family function", "pending"),
                ("EMP2005", "sick", 2, 2, "Fever", "pending"),
                ("EMP1006", "earned", -20, 3, "Travel", "approved"),
                ("EMP2003", "casual", -9, 1, "Personal work", "rejected"),
            ]:
                s = self.today + timedelta(days=start)
                decided = status != "pending"
                self.db.add(
                    LeaveRequest(
                        school_id=self.sid,
                        staff_id=self.staff[code],
                        leave_type=lt,
                        starts_on=s,
                        ends_on=s + timedelta(days=days - 1),
                        reason=reason,
                        status=status,
                        decided_by_user_id=self.user_ids["DIR005"] if decided else None,
                        decided_at=datetime.now(UTC) - timedelta(days=10) if decided else None,
                        decision_comment="Approved."
                        if status == "approved"
                        else "Exams scheduled that day."
                        if decided
                        else None,
                    )
                )
        if _empty(self.db, StaffDuty):
            for code, title, offset in [
                ("EMP2005", "Prepare PTM attendance sheets", 2),
                ("EMP2005", "Visitor register audit", 0),
                ("EMP2006", "Science lab inventory check", 1),
                ("EMP1002", "Exam invigilation: Hall 2", 4),
                ("EMP1001", "Morning assembly coordination", 0),
            ]:
                self.db.add(
                    StaffDuty(
                        school_id=self.sid, staff_id=self.staff[code], title=title, duty_date=self.today + timedelta(days=offset)
                    )
                )
        if _empty(self.db, Document):
            for owner_type, owner, title, cat in [
                ("school", None, "Term 2 academic calendar", "circular"),
                ("school", None, "Fee policy 2026-27", "policy"),
                ("staff", self.staff["EMP2005"], "Appointment letter", "hr_letter"),
                ("staff", self.staff["EMP1001"], "Appointment letter", "hr_letter"),
            ]:
                self.db.add(
                    Document(
                        school_id=self.sid,
                        owner_type=owner_type,
                        owner_id=owner,
                        title=title,
                        category=cat,
                        mime_type="application/pdf",
                    )
                )
        if _empty(self.db, AdmissionEnquiry):
            for name, grade in [("Sanjay Kumar", "Grade 6"), ("Fatima Ali", "Grade 8"), ("Ritu Sinha", "Grade 9")]:
                self.db.add(
                    AdmissionEnquiry(
                        school_id=self.sid,
                        parent_name=name,
                        email=f"{name.split()[0].lower()}@example.com",
                        phone="9000000000",
                        grade_sought=grade,
                        message="Please share the admission process.",
                    )
                )
        if _empty(self.db, EvaluationRubric):
            rubric = EvaluationRubric(
                school_id=self.sid,
                name="Teacher development rubric (demo)",
                criteria=[
                    {
                        "key": "learning_progress",
                        "label": "Student learning progress",
                        "max_score": 4,
                        "description": "Growth across assessments, considering starting points.",
                    },
                    {
                        "key": "curriculum_delivery",
                        "label": "Curriculum delivery",
                        "max_score": 4,
                        "description": "Planned topics delivered with appropriate pacing.",
                    },
                    {
                        "key": "student_support",
                        "label": "Student support",
                        "max_score": 4,
                        "description": "Follow-up with students who need help.",
                    },
                    {
                        "key": "professional_development",
                        "label": "Professional development",
                        "max_score": 4,
                        "description": "Training, reflection and collaboration.",
                    },
                    {
                        "key": "classroom_observation",
                        "label": "Classroom observation",
                        "max_score": 4,
                        "description": "Evidence from scheduled observations.",
                    },
                    {
                        "key": "student_feedback",
                        "label": "Aggregated student feedback",
                        "max_score": 4,
                        "description": "Only aggregated, minimum-group-size feedback.",
                    },
                ],
            )
            self.db.add(rubric)
            self.db.flush()
            self.db.add(
                TeacherEvaluation(
                    school_id=self.sid,
                    staff_id=self.staff["EMP1002"],
                    rubric_id=rubric.id,
                    period_label=f"{self.year.name} mid-year",
                    status="draft",
                    scores={"curriculum_delivery": 3},
                    evidence_notes="Observation scheduled for next month.",
                    created_by_user_id=self.user_ids["DIR002"],
                )
            )


def seed(opts: SeedOptions | None = None, db: Session | None = None) -> School:
    if get_settings().app_env == "production":
        raise SystemExit("Refusing to seed demo data in production.")
    own = db is None
    db = db or session_factory()()
    try:
        return Seeder(db, opts or SeedOptions()).run()
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    started = datetime.now()
    school = seed()
    print(
        f"Seeded demo school '{school.name}' ({school.slug}) in {(datetime.now() - started).total_seconds():.1f}s",
        file=sys.stderr,
    )
