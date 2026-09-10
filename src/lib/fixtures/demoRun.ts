import type { DemoRun, Finding, Persona, StageInfo } from "@/lib/types";
import { NIELSEN_VISIBILITY_OF_SYSTEM_STATUS, WCAG_2_5_8, WCAG_4_1_2 } from "./citations";

// The one fictional product every screen's dummy content hangs off
// (POC_SPEC.md §5). "Marlow" is invented for this POC — not a real
// company, not a real running site. No real crawl ever happens; there
// is nothing at this "URL."
const PRODUCT_NAME = "Marlow";

const PERSONAS: Persona[] = [
  {
    id: "accessibility",
    name: "Accessibility-focused",
    restriction:
      "Perceives the page only through its accessibility tree — never the screenshot, layout, or CSS. Navigates by keyboard only.",
  },
  {
    id: "motor",
    name: "Motor / age-related",
    restriction:
      "Sees the full page, but clicks imprecisely — small or tightly-packed targets are frequently missed before landing correctly.",
  },
];

const STAGES: StageInfo[] = [
  { id: "crawl", label: "Crawl", description: "Loads the target flow and captures its structure." },
  {
    id: "detect",
    label: "Persona attempts",
    description: "Each selected persona attempts the task under its own restriction.",
  },
  {
    id: "ground",
    label: "Ground",
    description: "Every candidate issue is checked against a real WCAG or Nielsen source before being reported.",
  },
  {
    id: "fix",
    label: "Propose fix",
    description: "A concrete, specific fix is drafted for issues that are mechanically addressable.",
  },
  {
    id: "sandbox",
    label: "Sandbox",
    description: "The fix is applied to an isolated copy of the page — never the live site.",
  },
  {
    id: "verify",
    label: "Verify",
    description: "The same persona re-attempts the task against the sandboxed copy to confirm the fix actually worked.",
  },
  {
    id: "aggregate",
    label: "Aggregate",
    description: "Findings across personas and runs are combined into one ranked report.",
  },
];

const FINDINGS: Finding[] = [
  // --- Accessibility persona -------------------------------------------
  {
    id: "a11y-checkout-continue-button",
    personaId: "accessibility",
    taskId: "checkout",
    severity: "high",
    title: "Checkout's “Continue to payment” button has no accessible name",
    observation:
      "The accessibility tree exposes this control as an unlabeled button — it has no text content and no aria-label, so the linearized reading order announces only “button” with nothing identifying its purpose.",
    recommendation:
      "Give the button a real accessible name — visible label text, or at minimum an aria-label of “Continue to payment” — so it's identifiable outside of its visual position.",
    citation: WCAG_4_1_2,
    showcase: {
      proposedFix:
        "Add aria-label=\"Continue to payment\" to the button, or replace the icon-only button with one that has visible text.",
      sandboxNote: "Applied to an isolated copy of the checkout page — the live site was never touched.",
      verifyResult: "pass",
    },
  },
  {
    id: "a11y-signup-password-requirements",
    personaId: "accessibility",
    taskId: "signup",
    severity: "medium",
    title: "Password requirements are only shown as placeholder text",
    observation:
      "The password requirements (“8+ characters, one number”) live inside the input as placeholder text, which disappears from the accessibility tree the moment the field is focused and typed into.",
    recommendation:
      "Move the requirements to persistent helper text, programmatically associated via aria-describedby, so they stay available throughout.",
  },
  {
    id: "a11y-signup-skip-link-order",
    personaId: "accessibility",
    taskId: "signup",
    severity: "low",
    title: "Skip-to-content link exists but isn't the first focusable element",
    observation:
      "A skip link is present, but three decorative elements receive focus before it, adding unnecessary tab stops for keyboard-only navigation.",
    recommendation: "Move the skip link to the very first position in the page's focus order.",
  },
  {
    id: "a11y-checkout-promo-no-confirmation",
    personaId: "accessibility",
    taskId: "checkout",
    severity: "medium",
    title: "No confirmation is announced after a promo code is applied",
    observation:
      "After entering a valid promo code and activating Apply, no visible or programmatically announced confirmation appears — the price simply changes with no status message.",
    recommendation:
      "Add a brief, programmatically announced confirmation (e.g. an aria-live region: “Promo code applied — $8 off”) so it isn't only a silent visual change.",
    citation: NIELSEN_VISIBILITY_OF_SYSTEM_STATUS,
  },

  // --- Motor / age-related persona --------------------------------------
  {
    id: "motor-checkout-apply-button-size",
    personaId: "motor",
    taskId: "checkout",
    severity: "high",
    title: "Promo code “Apply” button is smaller than a reliable tap target",
    observation:
      "The Apply button next to the promo code field measures roughly 18 by 18 CSS pixels. Across repeated attempts, the simulated imprecise pointer missed it or landed on an adjacent element first.",
    recommendation:
      "Increase the button to at least 24 by 24 CSS pixels, or add enough spacing that a near-miss doesn't trigger a neighboring control.",
    citation: WCAG_2_5_8,
    showcase: {
      proposedFix:
        "Increase the Apply button's clickable area to at least 24×24 CSS pixels and add 8px of spacing from the promo code input.",
      sandboxNote: "Applied to an isolated copy of the checkout page — the live site was never touched.",
      verifyResult: "pass",
    },
  },
  {
    id: "motor-signup-name-fields-spacing",
    personaId: "motor",
    taskId: "signup",
    severity: "medium",
    title: "First/last name fields sit only 4px apart",
    observation:
      "The “First name” and “Last name” fields are stacked with only 4px of vertical spacing; a near-miss click landed in the wrong field before self-correcting.",
    recommendation: "Increase spacing between adjacent form fields to at least 8px.",
  },
  {
    id: "motor-checkout-stepper-overlap",
    personaId: "motor",
    taskId: "checkout",
    severity: "low",
    title: "Quantity stepper's minus button occasionally registers as the input field",
    observation:
      "The imprecise pointer clicked the quantity input instead of the adjacent minus button in 2 of 5 attempts.",
    recommendation: "Add a small gap between the stepper buttons and the input, or enlarge the stepper buttons.",
  },
];

function severityCounts(findings: Finding[]) {
  return {
    highCount: findings.filter((f) => f.severity === "high").length,
    mediumCount: findings.filter((f) => f.severity === "medium").length,
    lowCount: findings.filter((f) => f.severity === "low").length,
  };
}

const CURRENT_COUNTS = severityCounts(FINDINGS);

export const demoRun: DemoRun = {
  productName: PRODUCT_NAME,
  ranAt: "2026-08-29",
  personas: PERSONAS,
  tasks: [
    { id: "signup", label: "Create an account" },
    { id: "checkout", label: "Complete a purchase" },
  ],
  stages: STAGES,
  findings: FINDINGS,
  uiScore: {
    // Fixed dummy numbers — no real computation runs anywhere in this
    // POC (POC_SPEC.md rule 1). composite is just their average,
    // rounded, not a formula the real system would necessarily use.
    visualDesign: 78,
    accessibilityVisual: 64,
    composite: 71,
  },
  // Prior runs only, most recent first, telling an improving-over-time
  // story so the regression/compare-runs UI (M9) has something to show.
  history: [
    { id: "run-2026-08-22", ranAt: "2026-08-22", uiScore: 61, highCount: 4, mediumCount: 4, lowCount: 3 },
    { id: "run-2026-08-15", ranAt: "2026-08-15", uiScore: 52, highCount: 6, mediumCount: 5, lowCount: 4 },
    { id: "run-2026-08-08", ranAt: "2026-08-08", uiScore: 44, highCount: 8, mediumCount: 6, lowCount: 5 },
  ],
};

// Sanity check, dev-only: keep the "current run" history entry implied
// by CURRENT_COUNTS visible for whoever edits FINDINGS later, so the
// summary strip and the findings list can't silently drift apart.
if (import.meta.env.DEV) {
  console.info("[fixtures] current run severity counts:", CURRENT_COUNTS);
}
