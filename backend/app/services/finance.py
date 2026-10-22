"""Fee ledger queries and payment recording.

Every balance is computed from invoice lines, payment allocations, payments and
refunds. There is no stored, independently editable balance anywhere.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, literal_column, select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError, bad_request, not_found
from app.models import Invoice, InvoiceLine, Payment, PaymentAllocation, Refund, StudentProfile, Term
from app.schemas.finance import PaymentCreate
from app.services import audit
from app.services.auth_context import AuthContext
from app.services.lookups import money
from app.services.school import school_today

ZERO = Decimal("0.00")


def invoice_totals(db: Session, invoice_ids: list[UUID]) -> dict[UUID, dict[str, Decimal]]:
    if not invoice_ids:
        return {}
    signed = case((InvoiceLine.line_type == "concession", -InvoiceLine.amount), else_=InvoiceLine.amount)
    lines = db.execute(
        select(
            InvoiceLine.invoice_id,
            func.sum(case((InvoiceLine.line_type == "charge", InvoiceLine.amount), else_=0)),
            func.sum(case((InvoiceLine.line_type == "concession", InvoiceLine.amount), else_=0)),
            func.sum(case((InvoiceLine.line_type == "adjustment", InvoiceLine.amount), else_=0)),
            func.sum(signed),
        )
        .where(InvoiceLine.invoice_id.in_(invoice_ids))
        .group_by(InvoiceLine.invoice_id)
    )
    allocated = dict(
        db.execute(
            select(PaymentAllocation.invoice_id, func.sum(PaymentAllocation.amount))
            .where(PaymentAllocation.invoice_id.in_(invoice_ids))
            .group_by(PaymentAllocation.invoice_id)
        )
        .tuples()
        .all()
    )
    out: dict[UUID, dict[str, Decimal]] = {}
    for iid, charges, concessions, adjustments, net in lines:
        paid = allocated.get(iid) or ZERO
        out[iid] = {
            "charges": charges or ZERO,
            "concessions": concessions or ZERO,
            "adjustments": adjustments or ZERO,
            "net": net or ZERO,
            "paid": paid,
            "balance": (net or ZERO) - paid,
        }
    for iid in invoice_ids:
        out.setdefault(
            iid, {"charges": ZERO, "concessions": ZERO, "adjustments": ZERO, "net": ZERO, "paid": ZERO, "balance": ZERO}
        )
    return out


def invoice_status(inv: Invoice, totals: dict[str, Decimal], today: date) -> str:
    if inv.status == "cancelled":
        return "cancelled"
    if totals["balance"] <= 0:
        return "paid"
    if inv.due_on < today:
        return "overdue"
    return "partially_paid" if totals["paid"] > 0 else "unpaid"


def _invoice_out(inv: Invoice, t: dict[str, Decimal], today: date, terms: dict[UUID, str]) -> dict[str, Any]:
    return {
        "id": inv.id,
        "invoice_no": inv.invoice_no,
        "term": terms.get(inv.term_id) if inv.term_id else None,
        "issued_on": inv.issued_on,
        "due_on": inv.due_on,
        "status": invoice_status(inv, t, today),
        "charges": money(t["charges"]),
        "concessions": money(t["concessions"]),
        "adjustments": money(t["adjustments"]),
        "net": money(t["net"]),
        "paid": money(t["paid"]),
        "balance": money(t["balance"]),
    }


def get_student_ledger(db: Session, student_id: UUID, today: date) -> dict[str, Any]:
    invoices = list(db.scalars(select(Invoice).where(Invoice.student_id == student_id).order_by(Invoice.issued_on)))
    totals = invoice_totals(db, [i.id for i in invoices])
    terms = dict(db.execute(select(Term.id, Term.name)).tuples().all())
    lines: dict[UUID, list[dict[str, Any]]] = defaultdict(list)
    for ln in db.scalars(select(InvoiceLine).where(InvoiceLine.invoice_id.in_([i.id for i in invoices]))):
        lines[ln.invoice_id].append({"description": ln.description, "line_type": ln.line_type, "amount": money(ln.amount)})
    payments = list(db.scalars(select(Payment).where(Payment.student_id == student_id).order_by(Payment.paid_on)))
    pay_ids = [p.id for p in payments]
    allocs: dict[UUID, list[dict[str, Any]]] = defaultdict(list)
    inv_no = {i.id: i.invoice_no for i in invoices}
    for a in db.scalars(select(PaymentAllocation).where(PaymentAllocation.payment_id.in_(pay_ids))):
        allocs[a.payment_id].append({"invoice_no": inv_no.get(a.invoice_id), "amount": money(a.amount)})
    refunds = list(db.scalars(select(Refund).where(Refund.payment_id.in_(pay_ids)).order_by(Refund.refunded_on)))
    receipt = {p.id: p.receipt_no for p in payments}
    active = [i for i in invoices if i.status != "cancelled"]
    billed = sum((totals[i.id]["net"] for i in active), ZERO)
    paid = sum((p.amount for p in payments), ZERO)
    refunded = sum((r.amount for r in refunds), ZERO)
    upcoming = [i for i in active if totals[i.id]["balance"] > 0]
    return {
        "invoices": [{**_invoice_out(i, totals[i.id], today, terms), "lines": lines[i.id]} for i in invoices],
        "payments": [
            {
                "id": p.id,
                "receipt_no": p.receipt_no,
                "amount": money(p.amount),
                "paid_on": p.paid_on,
                "method": p.method,
                "reference": p.reference,
                "allocations": allocs[p.id],
            }
            for p in payments
        ],
        "refunds": [
            {"receipt_no": receipt[r.payment_id], "amount": money(r.amount), "refunded_on": r.refunded_on, "reason": r.reason}
            for r in refunds
        ],
        "totals": {
            "billed": money(billed),
            "concessions": money(sum((totals[i.id]["concessions"] for i in active), ZERO)),
            "paid": money(paid),
            "refunded": money(refunded),
            "outstanding": money(billed - paid + refunded),
        },
        "next_due": (
            {
                "invoice_no": upcoming[0].invoice_no,
                "due_on": upcoming[0].due_on,
                "balance": money(totals[upcoming[0].id]["balance"]),
            }
            if upcoming
            else None
        ),
    }


def get_school_summary(db: Session, today: date) -> dict[str, Any]:
    signed = case((InvoiceLine.line_type == "concession", -InvoiceLine.amount), else_=InvoiceLine.amount)
    billed = (
        db.scalar(
            select(func.coalesce(func.sum(signed), 0))
            .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
            .where(Invoice.status == "issued")
        )
        or ZERO
    )
    concessions = (
        db.scalar(
            select(func.coalesce(func.sum(InvoiceLine.amount), 0))
            .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
            .where(Invoice.status == "issued", InvoiceLine.line_type == "concession")
        )
        or ZERO
    )
    collected = db.scalar(select(func.coalesce(func.sum(Payment.amount), 0))) or ZERO
    refunded = db.scalar(select(func.coalesce(func.sum(Refund.amount), 0))) or ZERO
    allocated_sq = (
        select(PaymentAllocation.invoice_id, func.sum(PaymentAllocation.amount).label("paid"))
        .group_by(PaymentAllocation.invoice_id)
        .subquery()
    )
    net_sq = select(InvoiceLine.invoice_id, func.sum(signed).label("net")).group_by(InvoiceLine.invoice_id).subquery()
    overdue = db.execute(
        select(func.count(), func.coalesce(func.sum(net_sq.c.net - func.coalesce(allocated_sq.c.paid, 0)), 0))
        .select_from(Invoice)
        .join(net_sq, net_sq.c.invoice_id == Invoice.id)
        .outerjoin(allocated_sq, allocated_sq.c.invoice_id == Invoice.id)
        .where(Invoice.status == "issued", Invoice.due_on < today, net_sq.c.net - func.coalesce(allocated_sq.c.paid, 0) > 0)
    ).one()
    monthly = db.execute(
        select(func.to_char(Payment.paid_on, literal_column("'YYYY-MM'")), func.sum(Payment.amount))
        .group_by(func.to_char(Payment.paid_on, literal_column("'YYYY-MM'")))
        .order_by(func.to_char(Payment.paid_on, literal_column("'YYYY-MM'")))
    )
    return {
        "billed_net": money(billed),
        "concessions": money(concessions),
        "collected": money(collected),
        "refunded": money(refunded),
        "outstanding": money(billed - collected + refunded),
        "overdue_invoices": overdue[0],
        "overdue_amount": money(overdue[1]),
        "collection_rate_percent": round(float((collected - refunded) / billed * 100), 1) if billed else None,
        "monthly_collection": [{"month": m, "amount": money(a)} for m, a in monthly],
    }


def list_invoices(db: Session, today: date, query: str | None, status: str | None, page: int, page_size: int) -> dict[str, Any]:
    stmt = (
        select(Invoice, StudentProfile.student_code, StudentProfile.first_name, StudentProfile.last_name)
        .join(StudentProfile, StudentProfile.id == Invoice.student_id)
        .order_by(Invoice.invoice_no)
    )
    if query:
        like = f"%{query.strip()}%"
        stmt = stmt.where(
            StudentProfile.student_code.ilike(like)
            | StudentProfile.first_name.ilike(like)
            | StudentProfile.last_name.ilike(like)
            | Invoice.invoice_no.ilike(like)
        )
    rows = db.execute(stmt).tuples().all()
    totals = invoice_totals(db, [r[0].id for r in rows])
    terms = dict(db.execute(select(Term.id, Term.name)).tuples().all())
    items = [
        {**_invoice_out(inv, totals[inv.id], today, terms), "student_code": code, "student_name": f"{f} {l}"}
        for inv, code, f, l in rows
    ]
    if status:
        items = [i for i in items if i["status"] == status]
    start = (page - 1) * page_size
    return {"items": items[start : start + page_size], "total": len(items), "page": page, "page_size": page_size}


def record_payment(ctx: AuthContext, body: PaymentCreate) -> dict[str, Any]:
    db = ctx.db
    inv = db.scalar(select(Invoice).where(Invoice.id == body.invoice_id).with_for_update())
    if inv is None:
        raise not_found("Invoice")
    if inv.status == "cancelled":
        raise bad_request("Payments cannot be recorded against a cancelled invoice.")
    if body.paid_on > school_today(ctx.school) or body.paid_on < inv.issued_on:
        raise bad_request("The payment date must be between the invoice date and today.")
    balance = invoice_totals(db, [inv.id])[inv.id]["balance"]
    if body.amount > balance:
        raise AppError(409, "exceeds_balance", f"The amount exceeds the outstanding balance of {money(balance)}.")
    # Serialise receipt numbering per school inside this transaction.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"receipt:{ctx.school_id}"})
    count = db.scalar(select(func.count()).select_from(Payment)) or 0
    receipt_no = f"RCPT-{school_today(ctx.school).year}-{count + 1:05d}"
    while db.scalar(select(Payment.id).where(Payment.receipt_no == receipt_no)):
        count += 1
        receipt_no = f"RCPT-{school_today(ctx.school).year}-{count + 1:05d}"
    p = Payment(
        school_id=ctx.school_id,
        student_id=inv.student_id,
        receipt_no=receipt_no,
        amount=body.amount,
        paid_on=body.paid_on,
        method=body.method,
        reference=body.reference,
        received_by_user_id=ctx.user_id,
    )
    db.add(p)
    db.flush()
    db.add(PaymentAllocation(school_id=ctx.school_id, payment_id=p.id, invoice_id=inv.id, amount=body.amount))
    audit.record(
        db,
        ctx.school_id,
        "finance.payment_recorded",
        actor_user_id=ctx.user_id,
        entity_type="payment",
        entity_id=p.id,
        ip=ctx.ip,
        details={"invoice_no": inv.invoice_no, "amount": money(body.amount), "method": body.method},
    )
    db.commit()
    return {"receipt_no": receipt_no, "amount": money(body.amount), "new_balance": money(balance - body.amount)}
