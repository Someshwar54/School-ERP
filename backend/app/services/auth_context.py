"""The authenticated actor for one request: user, school, permissions and linked profile ids.

Built by app.api.deps.get_auth; passed to services so business rules never depend on HTTP."""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import forbidden
from app.models import AuthSession, School, User


@dataclass
class AuthContext:
    db: Session
    school: School
    user: User
    session: AuthSession
    permissions: frozenset[str]
    ip: str
    student_id: UUID | None = None
    staff_id: UUID | None = None
    _cache: dict[str, object] = field(default_factory=dict)

    @property
    def school_id(self) -> UUID:
        return self.school.id

    @property
    def user_id(self) -> UUID:
        return self.user.id

    def has(self, permission: str) -> bool:
        return permission in self.permissions

    def require(self, *permissions: str) -> None:
        """Require at least one of the given permissions."""
        if not any(p in self.permissions for p in permissions):
            raise forbidden()
