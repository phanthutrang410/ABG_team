"""H34b — deterministic briefing catalog + one-time shown/ack receipts.

Message + action-card copy is a pure function of `WeeklyReport` aggregates
and `role`; no OpenAI/LLM call is on this path, so a briefing exists even
when the provider is off (architecture doc 13 §9.2, brief `H34b`).
`WeeklyReport`/`Briefing` never carry `student_ref` — see
`app.contracts.integration.FORBIDDEN_PUBLIC_FIELDS` for the shared scan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Literal, Optional, Tuple

from app.weekly.report import WeeklyReport

Role = Literal["ban_quan_ly", "gvcn"]


@dataclass(frozen=True)
class ActionCard:
    """Backend-issued capability card — no raw URL/tool-call from the model."""

    key: str
    label_vi: str
    route_key: str


@dataclass(frozen=True)
class Briefing:
    """Role-scoped weekly briefing — deterministic, aggregate-only content."""

    briefing_id: str
    report_id: str
    role: Role
    message_vi: str
    action_cards: List[ActionCard] = field(default_factory=list)


@dataclass
class BriefingReceipt:
    """One row per `(user_id, role, briefing_id)` — "shown once" semantics."""

    user_id: str
    role: Role
    briefing_id: str
    shown_at: Optional[datetime] = None
    ack_at: Optional[datetime] = None


def _leader_cards(new_count: int) -> List[ActionCard]:
    return [
        ActionCard(key="open_weekly_report", label_vi="Xem báo cáo tuần", route_key="reports.weekly"),
        ActionCard(
            key="filter_new_detections",
            label_vi=f"Xem {new_count} tín hiệu mới",
            route_key="reports.weekly.new",
        ),
        ActionCard(
            key="open_advisor_drafts",
            label_vi="Soạn thông báo cho GVCN (bản nháp)",
            route_key="notify",
        ),
    ]


def _advisor_cards(new_count: int) -> List[ActionCard]:
    return [
        ActionCard(
            key="view_weekly_briefing", label_vi="Xem case được giao", route_key="my-class"
        ),
        ActionCard(
            key="filter_new_detections",
            label_vi=f"Xem {new_count} tín hiệu mới trong case được giao",
            route_key="my-class.new",
        ),
    ]


def _message_vi(report: WeeklyReport, role: Role) -> str:
    a = report.aggregates
    scope = "case được giao" if role == "gvcn" else "case"
    if report.status == "empty":
        return f"Chưa có tín hiệu nào trong báo cáo tuần này ({scope})."
    if report.status == "baseline_unavailable":
        return (
            f"Đây là lần chạy đầu tiên có thể so sánh — {a.get('total_active', 0)} {scope} đang mở. "
            "Chưa có dữ liệu tuần trước để tính tín hiệu mới."
        )
    if report.status == "failed":
        return (
            f"Không tính được báo cáo tuần này ({scope}); đang hiển thị lần thành công gần nhất."
        )
    if report.status == "stale":
        return (
            f"Dữ liệu tuần này đang cũ hơn dự kiến. Lần thành công gần nhất có "
            f"{a.get('new', 0)} tín hiệu mới, {a.get('ongoing', 0)} {scope} đang theo dõi, "
            f"{a.get('changed', 0)} {scope} có thay đổi."
        )
    return (
        f"Tuần này có {a.get('new', 0)} tín hiệu mới cần rà soát, {a.get('ongoing', 0)} {scope} "
        f"đang theo dõi và {a.get('changed', 0)} {scope} có thay đổi. "
        f"Tổng {a.get('total_active', 0)} {scope} đang mở."
    )


def _build_briefing(report: WeeklyReport, role: Role, briefing_id: str) -> Briefing:
    new_count = report.aggregates.get("new", 0)
    cards = _leader_cards(new_count) if role == "ban_quan_ly" else _advisor_cards(new_count)
    return Briefing(
        briefing_id=briefing_id,
        report_id=report.report_id,
        role=role,
        message_vi=_message_vi(report, role),
        action_cards=cards,
    )


class BriefingStore:
    """Thread-safe MVP store for briefings + one-time receipts."""

    def __init__(self) -> None:
        self._briefings: Dict[str, Briefing] = {}
        self._receipts: Dict[Tuple[str, str, str], BriefingReceipt] = {}
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._briefings.clear()
            self._receipts.clear()

    def get_or_create_briefing(self, report: WeeklyReport, role: Role) -> Briefing:
        briefing_id = f"br-{report.report_id}-{role}"
        with self._lock:
            existing = self._briefings.get(briefing_id)
            if existing is not None:
                return existing
            briefing = _build_briefing(report, role, briefing_id)
            self._briefings[briefing_id] = briefing
            return briefing

    def get_receipt(self, user_id: str, role: Role, briefing_id: str) -> Optional[BriefingReceipt]:
        with self._lock:
            return self._receipts.get((user_id, role, briefing_id))

    def mark_shown(self, user_id: str, role: Role, briefing_id: str) -> BriefingReceipt:
        key = (user_id, role, briefing_id)
        with self._lock:
            receipt = self._receipts.get(key)
            if receipt is None:
                receipt = BriefingReceipt(user_id=user_id, role=role, briefing_id=briefing_id)
                self._receipts[key] = receipt
            if receipt.shown_at is None:
                receipt.shown_at = datetime.now(timezone.utc)
            return receipt

    def mark_ack(self, user_id: str, role: Role, briefing_id: str) -> BriefingReceipt:
        key = (user_id, role, briefing_id)
        with self._lock:
            receipt = self._receipts.get(key)
            if receipt is None:
                receipt = BriefingReceipt(user_id=user_id, role=role, briefing_id=briefing_id)
                self._receipts[key] = receipt
            if receipt.ack_at is None:
                receipt.ack_at = datetime.now(timezone.utc)
            return receipt


def get_or_create_briefing(store: BriefingStore, report: WeeklyReport, role: Role) -> Briefing:
    return store.get_or_create_briefing(report, role)


def mark_shown(store: BriefingStore, user_id: str, role: Role, briefing_id: str) -> BriefingReceipt:
    return store.mark_shown(user_id, role, briefing_id)


def mark_ack(store: BriefingStore, user_id: str, role: Role, briefing_id: str) -> BriefingReceipt:
    return store.mark_ack(user_id, role, briefing_id)
