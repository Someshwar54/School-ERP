"""Typed school operational settings, validated before they are stored."""

from pydantic import BaseModel, Field, field_validator

ERP_MODULES = (
    "attendance",
    "academics",
    "timetable",
    "fees",
    "announcements",
    "events",
    "documents",
    "messaging",
    "complaints",
    "feedback",
    "lesson_progress",
    "library",
    "transport",
    "payroll",
)


class GradeBand(BaseModel):
    min_percent: float = Field(ge=0, le=100)
    grade: str = Field(min_length=1, max_length=4)


class Terminology(BaseModel):
    student: str = "Student"
    staff: str = "Staff"
    class_teacher: str = "Class Teacher"
    section: str = "Section"
    director: str = "Director"


class AcademicSettings(BaseModel):
    pass_percent: float = Field(default=33, ge=0, le=100)
    attendance_alert_percent: float = Field(default=75, ge=0, le=100)
    low_performance_percent: float = Field(default=40, ge=0, le=100)
    grade_scale: list[GradeBand] = [
        GradeBand(min_percent=91, grade="A1"),
        GradeBand(min_percent=81, grade="A2"),
        GradeBand(min_percent=71, grade="B1"),
        GradeBand(min_percent=61, grade="B2"),
        GradeBand(min_percent=51, grade="C1"),
        GradeBand(min_percent=41, grade="C2"),
        GradeBand(min_percent=33, grade="D"),
        GradeBand(min_percent=0, grade="E"),
    ]

    @field_validator("grade_scale")
    @classmethod
    def _sorted_with_floor(cls, v: list[GradeBand]) -> list[GradeBand]:
        bands = sorted(v, key=lambda b: b.min_percent, reverse=True)
        if not bands or bands[-1].min_percent != 0:
            raise ValueError("grade_scale must include a band starting at 0")
        return bands


class AttendancePolicy(BaseModel):
    weekly_off_days: list[int] = Field(default=[6], description="0=Monday ... 6=Sunday")
    count_late_as_present: bool = True
    # Approved leave / excused absence are excluded from the denominator when True.
    exclude_authorised_absence: bool = True
    correction_window_days: int = Field(default=7, ge=0, le=60)
    period_attendance_enabled: bool = True

    @field_validator("weekly_off_days")
    @classmethod
    def _valid_days(cls, v: list[int]) -> list[int]:
        if any(d < 0 or d > 6 for d in v):
            raise ValueError("weekly_off_days must be between 0 and 6")
        return sorted(set(v))


class RegionalSettings(BaseModel):
    timezone: str = "Asia/Kolkata"
    locale: str = "en-IN"
    currency: str = "INR"
    date_format: str = "DD MMM YYYY"


class SchoolSettingsModel(BaseModel):
    enabled_modules: list[str] = list(ERP_MODULES[:11])
    terminology: Terminology = Terminology()
    academic: AcademicSettings = AcademicSettings()
    attendance: AttendancePolicy = AttendancePolicy()
    regional: RegionalSettings = RegionalSettings()

    @field_validator("enabled_modules")
    @classmethod
    def _known_modules(cls, v: list[str]) -> list[str]:
        unknown = set(v) - set(ERP_MODULES)
        if unknown:
            raise ValueError(f"unknown modules: {sorted(unknown)}")
        return sorted(set(v), key=ERP_MODULES.index)
