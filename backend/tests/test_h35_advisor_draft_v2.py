"""H35 — advisor draft v2 on durable approved/assigned episodes (server scope)."""

from __future__ import annotations

import dataclasses

import pytest

from app.auth.principal import Principal
from app.contracts.advisor_handoff_draft import assert_no_handoff_forbidden_keys
from app.weekly.advisor_draft_v2 import build_advisor_drafts_v2
from app.weekly.cases_durable import CaseRepository

_LEADER_A = Principal(actor_id="leader:1", active_role="leader", org_scope="org-a", advisor_scope=None)
_ADVISOR_1 = Principal(
    actor_id="advisor:1", active_role="advisor", org_scope="org-a", advisor_scope="adv-1"
)
_ADVISOR_2 = Principal(
    actor_id="advisor:2", active_role="advisor", org_scope="org-a", advisor_scope="adv-2"
)


def _approve_and_assign(repo: CaseRepository, student_ref: str, *, advisor_ref: str, org_scope: str = "org-a"):
    episode = repo.create_episode(student_ref, "semester", org_scope=org_scope)
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    repo.transition(episode.episode_id, "assign", actor="leader:demo", advisor_ref=advisor_ref)
    return repo.get(episode.episode_id)


def _approve_only(repo: CaseRepository, student_ref: str, *, org_scope: str = "org-a"):
    episode = repo.create_episode(student_ref, "semester", org_scope=org_scope)
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    return repo.get(episode.episode_id)


def test_only_approved_and_assigned_states_included() -> None:
    repo = CaseRepository()
    pending = repo.create_episode("s-pending", "semester", org_scope="org-a")
    approved = _approve_only(repo, "s-approved")
    assigned = _approve_and_assign(repo, "s-assigned", advisor_ref="adv-1")
    dismissed_ep = repo.create_episode("s-dismissed", "semester", org_scope="org-a")
    repo.transition(dismissed_ep.episode_id, "dismiss", actor="leader:demo", reason_code="resolved_offline")

    response = build_advisor_drafts_v2(repo, "wr-1", _LEADER_A)

    all_episode_ids = {
        c.episode_id
        for bundle in response.bundles
        for c in bundle.cases
    } | {c.episode_id for c in response.mapping_repair.cases}

    assert pending.episode_id not in all_episode_ids
    assert dismissed_ep.episode_id not in all_episode_ids
    assert approved.episode_id in all_episode_ids
    assert assigned.episode_id in all_episode_ids


def test_group_by_advisor_ref() -> None:
    repo = CaseRepository()
    _approve_and_assign(repo, "s-1", advisor_ref="adv-1")
    _approve_and_assign(repo, "s-2", advisor_ref="adv-1")
    _approve_and_assign(repo, "s-3", advisor_ref="adv-2")

    response = build_advisor_drafts_v2(repo, "wr-1", _LEADER_A)

    by_ref = {b.advisor_ref: b for b in response.bundles}
    assert set(by_ref) == {"adv-1", "adv-2"}
    assert by_ref["adv-1"].case_count == 2
    assert by_ref["adv-2"].case_count == 1
    assert response.mapping_repair.case_count == 0


def test_missing_advisor_ref_goes_to_mapping_repair_bucket() -> None:
    repo = CaseRepository()
    approved_no_advisor = _approve_only(repo, "s-no-advisor")

    response = build_advisor_drafts_v2(repo, "wr-1", _LEADER_A)

    assert response.bundles == []
    assert response.mapping_repair.case_count == 1
    assert response.mapping_repair.cases[0].episode_id == approved_no_advisor.episode_id
    assert "mapping_repair" in response.mapping_repair.limitations


def test_cross_org_episode_excluded_for_leader() -> None:
    repo = CaseRepository()
    _approve_and_assign(repo, "s-other-org", advisor_ref="adv-1", org_scope="org-b")

    response = build_advisor_drafts_v2(repo, "wr-1", _LEADER_A)

    assert response.state == "empty"
    assert response.bundles == []
    assert response.mapping_repair.case_count == 0


def test_advisor_sees_only_own_assigned_cases() -> None:
    repo = CaseRepository()
    mine = _approve_and_assign(repo, "s-mine", advisor_ref="adv-1")
    _approve_and_assign(repo, "s-other", advisor_ref="adv-2")

    response = build_advisor_drafts_v2(repo, "wr-1", _ADVISOR_1)

    assert len(response.bundles) == 1
    assert response.bundles[0].advisor_ref == "adv-1"
    assert [c.episode_id for c in response.bundles[0].cases] == [mine.episode_id]


def test_advisor_cross_advisor_scope_denied() -> None:
    repo = CaseRepository()
    _approve_and_assign(repo, "s-1", advisor_ref="adv-1")

    response = build_advisor_drafts_v2(repo, "wr-1", _ADVISOR_2)

    assert response.state == "empty"
    assert response.bundles == []


def test_requires_human_approval_always_true() -> None:
    repo = CaseRepository()
    _approve_and_assign(repo, "s-1", advisor_ref="adv-1")

    response = build_advisor_drafts_v2(repo, "wr-1", _LEADER_A)

    assert len(response.bundles) == 1
    assert response.bundles[0].requires_human_approval is True


def test_empty_state_when_no_eligible_episodes() -> None:
    repo = CaseRepository()
    repo.create_episode("s-1", "semester", org_scope="org-a")  # pending_review only

    response = build_advisor_drafts_v2(repo, "wr-1", _LEADER_A)

    assert response.state == "empty"
    assert response.bundles == []
    assert response.mapping_repair.case_count == 0


def test_no_forbidden_public_fields_and_no_pii_in_draft_text() -> None:
    repo = CaseRepository()
    _approve_and_assign(repo, "s-1", advisor_ref="adv-1")
    _approve_only(repo, "s-2")

    response = build_advisor_drafts_v2(repo, "wr-1", _LEADER_A)
    payload = dataclasses.asdict(response)
    # advisor_ref is an allowed routing exception here, same as H22.
    assert_no_handoff_forbidden_keys(payload)

    blob = str(payload).lower()
    for token in ("email", "phone", "full_name", "mssv", "@", "sđt"):
        assert token not in blob


def test_no_send_route_or_function_exists() -> None:
    import app.weekly.advisor_draft_v2 as mod

    assert not hasattr(mod, "router")
    assert not any("send" in name.lower() for name in dir(mod))


def test_forbidden_vocabulary_raises() -> None:
    from app.weekly.advisor_draft_v2 import AdvisorDraftV2CaseLine, build_draft_preview_vi

    bad_line = AdvisorDraftV2CaseLine(
        episode_id="ep-1", student_ref="nguy cơ bỏ học", branch="semester", case_state="approved"
    )
    with pytest.raises(ValueError):
        build_draft_preview_vi([bad_line])
