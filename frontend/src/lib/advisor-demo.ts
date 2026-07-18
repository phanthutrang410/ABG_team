import type { CaseState, ReviewCase } from "./types";

/**
 * UI-only fixture for the advisor experience.
 *
 * This is deliberately separate from the validated API fixtures: it never
 * pretends to be a backend response or an RBAC decision. All identifiers are
 * generated pseudonyms, all cases have already been handed off, and the
 * advisor never receives a priority band/raw score.
 */
export type AdvisorDemoCase = ReviewCase & {
  assigned_at: string;
  updated_at: string;
  monitoring_until: string | null;
};

export type AdvisorDemoAction = "accept" | "monitor" | "resolve";

export type AdvisorDemoStudent = {
  student_ref: string;
  class_code: string;
  case_id: string | null;
  case_state: CaseState | null;
  updated_at: string | null;
};

export type AdvisorDemoClass = {
  class_code: string;
  term_code: string;
  students: AdvisorDemoStudent[];
};

export type AdvisorFollowUpKind = "accept_handoff" | "continue_support" | "monitoring_check";

export type AdvisorFollowUpItem = {
  case_id: string;
  student_ref: string;
  case_state: CaseState;
  kind: AdvisorFollowUpKind;
  due_at: string;
};

const HANDED_OFF_STATES: CaseState[] = [
  "assigned",
  "assigned",
  "follow_up_in_progress",
  "follow_up_in_progress",
  "monitoring",
  "resolved",
  "follow_up_in_progress",
  "resolved",
];

const GRADE_FACTOR_CODES = [
  "grade_trend_declining",
  "grade_volatility_elevated",
] as const;

function hashSeed(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function isoOffset(base: Date, days: number, hours = 0): string {
  return new Date(base.getTime() + days * 86_400_000 + hours * 3_600_000).toISOString();
}

function pseudoRef(random: () => number, index: number): string {
  const token = Math.floor(random() * 0xffffff).toString(16).padStart(6, "0");
  return `sv-demo-${token}-${String(index + 1).padStart(2, "0")}`;
}

export function generateAdvisorDemoClasses(
  accountId: string,
  variant: number,
  cases: readonly AdvisorDemoCase[],
): AdvisorDemoClass[] {
  const random = seededRandom(hashSeed(`${accountId}:classes:${variant}`));
  const classCodes = ["K66-CNTT-A", "K66-CNTT-B"];
  const rosters: AdvisorDemoClass[] = classCodes.map((classCode) => ({
    class_code: classCode,
    term_code: "20251",
    students: [],
  }));

  cases.forEach((item, index) => {
    const target = rosters[index % rosters.length];
    target.students.push({
      student_ref: item.student_ref,
      class_code: target.class_code,
      case_id: item.case_id,
      case_state: item.case_state,
      updated_at: item.updated_at,
    });
  });

  rosters.forEach((roster, classIndex) => {
    while (roster.students.length < 12) {
      const rowIndex = roster.students.length;
      const token = Math.floor(random() * 0xffffff).toString(16).padStart(6, "0");
      roster.students.push({
        student_ref: `sv-lop-${token}-${classIndex + 1}${String(rowIndex + 1).padStart(2, "0")}`,
        class_code: roster.class_code,
        case_id: null,
        case_state: null,
        updated_at: null,
      });
    }
    roster.students.sort((left, right) => left.student_ref.localeCompare(right.student_ref));
  });

  return rosters;
}

export function buildAdvisorFollowUps(
  cases: readonly AdvisorDemoCase[],
): AdvisorFollowUpItem[] {
  return cases
    .filter((item) => item.case_state !== "resolved")
    .map((item) => {
      if (item.case_state === "assigned") {
        return {
          case_id: item.case_id,
          student_ref: item.student_ref,
          case_state: item.case_state,
          kind: "accept_handoff" as const,
          due_at: isoOffset(new Date(item.assigned_at), 2),
        };
      }
      if (item.case_state === "monitoring") {
        return {
          case_id: item.case_id,
          student_ref: item.student_ref,
          case_state: item.case_state,
          kind: "monitoring_check" as const,
          due_at: item.monitoring_until ?? isoOffset(new Date(item.updated_at), 7),
        };
      }
      return {
        case_id: item.case_id,
        student_ref: item.student_ref,
        case_state: item.case_state,
        kind: "continue_support" as const,
        due_at: isoOffset(new Date(item.updated_at), 7),
      };
    })
    .sort((left, right) => left.due_at.localeCompare(right.due_at));
}

export function generateAdvisorDemoCases(
  accountId: string,
  variant = 0,
  now: Date = new Date(),
): AdvisorDemoCase[] {
  const random = seededRandom(hashSeed(`${accountId}:${variant}`));

  return HANDED_OFF_STATES.map((caseState, index) => {
    const studentRef = pseudoRef(random, index);
    const factorCode = GRADE_FACTOR_CODES[index % GRADE_FACTOR_CODES.length];
    const assignedDaysAgo = 1 + index * 2 + Math.floor(random() * 3);
    const assignedAt = isoOffset(now, -assignedDaysAgo, -Math.floor(random() * 8));
    const updatedAt = caseState === "assigned"
      ? assignedAt
      : isoOffset(now, -Math.max(0, assignedDaysAgo - 1), -Math.floor(random() * 5));
    const monitoringUntil = caseState === "monitoring"
      ? isoOffset(now, 7 + Math.floor(random() * 8))
      : null;

    return {
      case_id: `demo-assignment-${variant}-${index + 1}-${studentRef.slice(-8)}`,
      student_ref: studentRef,
      case_state: caseState,
      // T3 sees the neutral handoff reason, not an ordering/risk band.
      review_priority_band: null,
      contributing_factors: [
        {
          code: factorCode,
          evidence_refs: [`term_avg:${index % 2 === 0 ? "20242" : "20241"}`, "term_avg:20251"],
        },
      ],
      coverage: {
        n_valid_terms: 2 + (index % 2),
        n_courses: 8 + Math.floor(random() * 7),
        // Do not synthesize attendance to fill a source/data gap.
        n_attendance_events: 0,
        last_term_code: "20251",
        last_attendance_at: null,
        status: "partial",
        reason_codes: ["attendance_source_unapproved"],
      },
      data_state: "partial",
      limitations: ["attendance_source_unapproved", "copy.partial_term_only"],
      dataset_version: "advisor-ui-demo:generated-pseudonymous",
      model_version: "demo-fixture-not-model-output",
      threshold_config_version: "demo-fixture-no-threshold",
      calculated_at: isoOffset(new Date(assignedAt), 0, -1),
      assigned_at: assignedAt,
      updated_at: updatedAt,
      monitoring_until: monitoringUntil,
    };
  });
}

export function allowedAdvisorDemoActions(caseState: CaseState): AdvisorDemoAction[] {
  if (caseState === "assigned") return ["accept"];
  if (caseState === "follow_up_in_progress") return ["monitor", "resolve"];
  if (caseState === "monitoring") return ["resolve"];
  return [];
}

export function transitionAdvisorDemoCase(
  item: AdvisorDemoCase,
  action: AdvisorDemoAction,
  now: Date = new Date(),
  monitoringUntil: string | null = null,
): AdvisorDemoCase {
  if (!allowedAdvisorDemoActions(item.case_state).includes(action)) {
    throw new Error(`forbidden_transition:${item.case_state}:${action}`);
  }

  if (action === "monitor" && !monitoringUntil) {
    throw new Error("missing_monitoring_until");
  }

  const nextState: CaseState = action === "accept"
    ? "follow_up_in_progress"
    : action === "monitor"
      ? "monitoring"
      : "resolved";

  return {
    ...item,
    case_state: nextState,
    updated_at: now.toISOString(),
    monitoring_until: action === "monitor" ? monitoringUntil : null,
  };
}

export function advisorDemoStorageKey(accountId: string): string {
  return `silentshield.advisor-demo.v1.${accountId}`;
}

/** Queue page size for the advisor "Hàng đợi của tôi" list (10 case / trang). */
export const ADVISOR_QUEUE_PAGE_SIZE = 10;

export type AdvisorQueuePage<T> = {
  page: number;
  totalPages: number;
  pageItems: T[];
  start: number;
  end: number;
  total: number;
};

/**
 * Pure, deterministic pagination for the advisor queue.
 *
 * Clamps `page` into `[1, totalPages]` so a filter/search change that shrinks
 * the list can never strand the view on an empty page. `start`/`end` are
 * 0-based/exclusive slice bounds; the UI shows `start + 1`–`end`.
 */
export function paginateAdvisorQueue<T>(
  items: readonly T[],
  page: number,
  pageSize: number = ADVISOR_QUEUE_PAGE_SIZE,
): AdvisorQueuePage<T> {
  const size = Math.max(1, Math.trunc(pageSize) || ADVISOR_QUEUE_PAGE_SIZE);
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / size));
  const clamped = Math.min(Math.max(1, Math.trunc(page) || 1), totalPages);
  const start = total === 0 ? 0 : (clamped - 1) * size;
  const end = Math.min(start + size, total);
  return { page: clamped, totalPages, pageItems: items.slice(start, end), start, end, total };
}
