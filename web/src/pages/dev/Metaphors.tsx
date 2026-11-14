// M5 verification page — dev-only, unlinked from any nav. Renders the
// three novel visual-metaphor components (nothing in the ported code
// had any precedent for these) at both scales so they can be checked
// before M7/M8/M10 build real screens around them. Must be
// removed/excluded from the production build and nav by M12.

import { AccessibilityRestrictedView } from "@/components/personas/AccessibilityRestrictedView";
import { MotorImprecisePointer } from "@/components/personas/MotorImprecisePointer";
import { VerifyStamp } from "@/components/VerifyStamp";

export default function Metaphors() {
  return (
    <div className="container space-y-14 py-12">
      <header>
        <p className="label-mono">M5 verification — dev only</p>
        <h1 className="mt-3 text-d1 font-hero">Persona restriction &amp; verify stamp</h1>
        <p className="mt-4 max-w-[62ch] text-ink-2">
          Check: does the blur genuinely read as "cannot see this," not just "blurry"? Does the
          cursor read as miss-then-correct, not aimless jitter? Does the stamp read as a physical
          mark? All three should also hold up with reduced motion enabled in system settings.
        </p>
      </header>

      <section>
        <h2 className="text-d3">Accessibility persona — thumbnail (at-rest, M7 card)</h2>
        <div className="mt-4">
          <AccessibilityRestrictedView size="thumbnail" />
        </div>
      </section>

      <section>
        <h2 className="text-d3">Accessibility persona — full (running state, M8)</h2>
        <div className="mt-4 max-w-2xl">
          <AccessibilityRestrictedView size="full" />
        </div>
      </section>

      <section>
        <h2 className="text-d3">Motor persona — icon (at-rest, M7 card)</h2>
        <div className="mt-4">
          <MotorImprecisePointer size="icon" />
        </div>
      </section>

      <section>
        <h2 className="text-d3">Motor persona — full, animated (running state, M8)</h2>
        <p className="mt-2 text-sm text-ink-3">
          Watch the cursor: it should move toward the promo area, land on the input (a miss),
          pause, then correct onto the tiny Apply button — looping.
        </p>
        <div className="mt-4">
          <MotorImprecisePointer size="full" />
        </div>
      </section>

      <section>
        <h2 className="text-d3">Verify stamp — pass / fail</h2>
        <div className="mt-4 flex flex-wrap gap-6">
          <VerifyStamp result="pass" />
          <VerifyStamp result="fail" />
        </div>
      </section>
    </div>
  );
}
