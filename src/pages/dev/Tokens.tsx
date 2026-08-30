// M1/M2 verification page — dev-only, unlinked from any nav. Renders
// every token and primitive these milestones touched so they can be
// checked visually before later milestones build on top of them. Must
// be removed/excluded from the production build and nav by M12 (see
// plan's M12 audit checklist).
//
// Rendered from App.tsx only when import.meta.env.DEV is true — there
// is no route to it, and it never ships in `npm run build`'s output
// bundle path since M4's real router won't reference it.

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";

function Swatch({ label, className }: { label: string; className: string }) {
  return (
    <div className="flex flex-col gap-2">
      <div className={`h-16 w-full rounded-md border border-rule ${className}`} />
      <span className="font-mono text-micro uppercase text-ink-3">{label}</span>
    </div>
  );
}

export default function Tokens() {
  return (
    <div className="container space-y-12 py-12">
      <header>
        <p className="label-mono">M1 verification — dev only</p>
        <h1 className="mt-3 text-d1 font-hero">SimUX design tokens</h1>
        <p className="mt-4 max-w-[60ch] text-ink-2">
          This page exists to check M1's token work before anything is built on
          top of it. It is not part of the product and must be gone by M12.
        </p>
      </header>

      <section>
        <h2 className="text-d3">Paper family (warmed per DESIGN.md)</h2>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
          <Swatch label="paper" className="bg-paper" />
          <Swatch label="paper-raised" className="bg-paper-raised" />
          <Swatch label="paper-sunk" className="bg-paper-sunk" />
        </div>
      </section>

      <section>
        <h2 className="text-d3">Stock tints (unchanged)</h2>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-5">
          <Swatch label="stock-1" className="bg-stock-1" />
          <Swatch label="stock-2" className="bg-stock-2" />
          <Swatch label="stock-3" className="bg-stock-3" />
          <Swatch label="stock-4" className="bg-stock-4" />
          <Swatch label="stock-5" className="bg-stock-5" />
        </div>
      </section>

      <section>
        <h2 className="text-d3">Severity (unchanged — must not collide with persona colors below)</h2>
        <div className="mt-4 grid grid-cols-3 gap-4">
          <Swatch label="critical" className="bg-critical" />
          <Swatch label="caution" className="bg-caution" />
          <Swatch label="minor" className="bg-minor" />
        </div>
      </section>

      <section>
        <h2 className="text-d3">Persona accents (new)</h2>
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="flex flex-col gap-2">
            <div className="flex h-16 w-full items-center justify-center rounded-md border border-rule bg-persona-accessibility">
              <span className="font-mono text-xs text-persona-accessibility-ink">Aa</span>
            </div>
            <span className="font-mono text-micro uppercase text-ink-3">accessibility</span>
          </div>
          <div className="flex flex-col gap-2">
            <div className="flex h-16 w-full items-center justify-center rounded-md border border-rule bg-persona-motor">
              <span className="font-mono text-xs text-persona-motor-ink">Aa</span>
            </div>
            <span className="font-mono text-micro uppercase text-ink-3">motor / age</span>
          </div>
          <div className="flex flex-col gap-2">
            <div className="flex h-16 w-full items-center justify-center rounded-md border border-rule bg-persona-phase2">
              <span className="font-mono text-xs text-persona-phase2-ink">Aa</span>
            </div>
            <span className="font-mono text-micro uppercase text-ink-3">phase 2 (mobile-first)</span>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-d3">Radius: two-tier system</h2>
        <div className="mt-4 flex flex-wrap items-end gap-4">
          <div className="h-20 w-20 rounded-sm border border-rule bg-paper-raised" />
          <div className="h-20 w-20 rounded-md border border-rule bg-paper-raised" />
          <div className="h-20 w-20 rounded-lg border border-rule bg-paper-raised" />
          <div className="h-24 w-24 rounded-xl border border-rule bg-paper-raised" />
          <div className="h-28 w-28 rounded-2xl border border-rule bg-paper-raised" />
        </div>
        <p className="mt-2 font-mono text-micro uppercase text-ink-3">
          sm · md · lg (tight, UI elements) — xl · 2xl (soft, section containers)
        </p>
      </section>

      <section>
        <h2 className="text-d3">Shadows</h2>
        <div className="mt-6 flex flex-wrap gap-8">
          <div className="h-20 w-32 rounded-lg bg-paper-raised shadow-chart" />
          <div className="h-20 w-32 rounded-lg bg-paper-raised shadow-lift" />
          <div className="h-20 w-32 rounded-lg bg-paper-raised shadow-stamp" />
          <div className="h-20 w-32 rounded-lg bg-paper-raised shadow-stamp-pass" />
          <div className="h-20 w-32 rounded-lg bg-paper-raised shadow-stamp-fail" />
        </div>
        <p className="mt-2 font-mono text-micro uppercase text-ink-3">
          chart · lift (soft ambient) — stamp · stamp-pass · stamp-fail (hard offset)
        </p>
      </section>

      <section>
        <h2 className="text-d3">Heading-font convention (three tiers)</h2>
        <h1 className="text-d1 font-display">Hero size, font-display (default — Bricolage)</h1>
        <h1 className="mt-4 text-d1 font-hero">
          Hero size, font-hero (Instrument Serif)
          <br />
          <span className="italic">mixed with its own italic.</span>
        </h1>
        <p className="mt-6 max-w-[60ch] text-ink-2">Body copy, font-body (Source Serif 4):</p>
        <p className="mt-2 max-w-[60ch] font-body text-ink-2">
          This is what a paragraph actually reads like — the readable workhorse serif,
          never swapped for Instrument Serif, which is reserved for display sizes only.
        </p>
        <p className="mt-4 max-w-[60ch] text-ink-2">
          Base rule keeps <code className="font-mono">font-display</code> (Bricolage
          Grotesque, swapped from Archivo — see index.html) as the default for all
          headings so in-card headings stay sans. Apply{" "}
          <code className="font-mono">font-hero</code> directly on hero-scale
          (<code className="font-mono">text-d1</code>/<code className="font-mono">text-d2</code>)
          headings for Instrument Serif&rsquo;s extra character — it wins via Tailwind's
          utility-over-base layer ordering, no extra override class needed. Pair it with
          a plain <code className="font-mono">italic</code> span for the roman+italic
          emphasis device (see Hero.tsx), matching wisprflow.ai's own headline treatment.{" "}
          <code className="font-mono">font-body</code> stays reserved for regular
          paragraph text, never reused for headings.
        </p>
      </section>

      <section>
        <h2 className="text-d3">card-chart vs. card-chart-lg</h2>
        <div className="mt-4 flex flex-wrap gap-6">
          <div className="card-chart w-64 p-4">card-chart (rounded-lg)</div>
          <div className="card-chart-lg w-64 p-4">card-chart-lg (rounded-2xl)</div>
        </div>
      </section>

      <section>
        <h2 className="text-d3">M2 — Buttons (press-down, not lift-up)</h2>
        <p className="mt-2 max-w-[60ch] text-ink-2">
          Click and hold any button below — it should scale down slightly
          (<code className="font-mono">scale(0.98)</code>), never lift up.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button variant="default">Default</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="link">Link</Button>
        </div>
        <div className="card-chart mt-4 flex flex-wrap items-center gap-3 bg-ink p-4">
          <Button variant="inverse">Inverse</Button>
          <Button variant="ghostInverse">Ghost inverse</Button>
          <Button variant="outlineInverse">Outline inverse</Button>
        </div>
      </section>

      <section>
        <h2 className="text-d3">M2 — Form primitives</h2>
        <div className="mt-4 grid max-w-md gap-5">
          <div>
            <Label htmlFor="tok-input">Example input (label-mono, genuinely code-like)</Label>
            <Input id="tok-input" className="mt-2" placeholder="https://example.com" />
          </div>
          <label className="flex items-center gap-2">
            <Checkbox defaultChecked />
            <span className="text-sm text-ink-2">Checkbox</span>
          </label>
          <label className="flex items-center gap-2">
            <Switch defaultChecked />
            <span className="text-sm text-ink-2">Switch</span>
          </label>
          <Separator />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
          <TokenCollapsible />
        </div>
      </section>

      <section>
        <h2 className="text-d3">M2 — Two label styles, side by side</h2>
        <div className="mt-4 flex flex-wrap gap-8">
          <div>
            <p className="label-mono">confidence 87%</p>
            <p className="mt-1 text-xs text-ink-3">
              .label-mono — genuinely code-like content (URLs, selectors, %s, citation IDs)
            </p>
          </div>
          <div>
            <p className="eyebrow-sans">Who it&rsquo;s for</p>
            <p className="mt-1 text-xs text-ink-3">
              .eyebrow-sans — editorial section labels (this is what SectionHeading uses now)
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function TokenCollapsible() {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <Button variant="outline" size="sm">
          {open ? "Hide" : "Show"} collapsible content
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-3 rounded-md border border-rule bg-paper-sunk p-3 text-sm text-ink-2">
        Expand/collapse should animate smoothly (collapsible-down/-up keyframes from M1&rsquo;s
        ported tailwind config).
      </CollapsibleContent>
    </Collapsible>
  );
}
