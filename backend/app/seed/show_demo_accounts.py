"""Print demo sign-in details for LOCAL DEVELOPMENT. Refuses to run in production.

python -m app.seed.show_demo_accounts
"""

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import session_factory, set_tenant
from app.models import School, StudentProfile
from app.seed import data


def main() -> None:
    if get_settings().app_env == "production" or not get_settings().demo_auth_mode:
        raise SystemExit("Demo accounts are only shown in local demo mode.")
    db = session_factory()()
    school = db.scalar(select(School).where(School.slug == "demo"))
    if school is None:
        raise SystemExit("Demo school not seeded. Run: python -m app.seed.demo")
    set_tenant(db, school.id)
    print(f"Demo accounts for {school.name} (fictional, local development only)\n")
    print("Students (password = registered phone number; prototype convention):")
    for code in ("STU0001", "STU0181", "STU0182", "STU0300"):
        s = db.scalar(select(StudentProfile).where(StudentProfile.student_code == code))
        if s:
            print(f"  {code}  {s.first_name} {s.last_name:<12}  password: {s.phone}")
    print("\nStaff (password = Staff@<last 4 digits of ID>):")
    for code, first, last, subj, _g, ct in data.TEACHERS[:4]:
        print(
            f"  {code}  {first} {last}  Teacher ({subj}){' + class teacher' if ct is not None else ''}  password: Staff@{code[-4:]}"
        )
    for code, first, last, desig, _dept, _roles in data.NON_TEACHING:
        print(f"  {code}  {first} {last}  {desig}  password: Staff@{code[-4:]}")
    print("\nManagement (password = Mgmt@<ID>):")
    for code, first, last, desig, _roles in data.MANAGEMENT:
        print(f"  {code}  {first} {last}  {desig}  password: Mgmt@{code}")
    db.close()


if __name__ == "__main__":
    main()
