/** @type {import('tailwindcss').Config} */
// Ported from site-doctor/frontend/tailwind.config.js, with DESIGN.md's
// adaptations applied as explicit additions (persona colors, the
// xl/2xl radius tier, the stamp shadows) rather than replacing anything
// that was already load-bearing there. See src/index.css for the token
// values these all resolve to.
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: { DEFAULT: "1.25rem", sm: "2rem", lg: "2.5rem" },
      screens: { "2xl": "1200px" },
    },
    extend: {
      colors: {
        paper: {
          DEFAULT: "hsl(var(--paper))",
          raised: "hsl(var(--paper-raised))",
          sunk: "hsl(var(--paper-sunk))",
        },
        stock: {
          1: "hsl(var(--stock-1))",
          2: "hsl(var(--stock-2))",
          3: "hsl(var(--stock-3))",
          4: "hsl(var(--stock-4))",
          5: "hsl(var(--stock-5))",
        },
        ink: {
          DEFAULT: "hsl(var(--ink))",
          2: "hsl(var(--ink-2))",
          3: "hsl(var(--ink-3))",
        },
        rule: "hsl(var(--rule))",
        critical: "hsl(var(--critical))",
        caution: "hsl(var(--caution))",
        minor: "hsl(var(--minor))",
        // NEW — persona accent tints. Reserved for persona-grouped
        // views only; never combined with severity/stock tinting on
        // the same card (see index.css's persona-token comment).
        persona: {
          accessibility: {
            DEFAULT: "hsl(var(--persona-accessibility))",
            ink: "hsl(var(--persona-accessibility-ink))",
          },
          motor: {
            DEFAULT: "hsl(var(--persona-motor))",
            ink: "hsl(var(--persona-motor-ink))",
          },
          phase2: {
            DEFAULT: "hsl(var(--persona-phase2))",
            ink: "hsl(var(--persona-phase2-ink))",
          },
        },
        // shadcn/ui compatibility aliases
        border: "hsl(var(--rule))",
        input: "hsl(var(--rule))",
        ring: "hsl(var(--ink))",
        background: "hsl(var(--paper))",
        foreground: "hsl(var(--ink))",
        primary: { DEFAULT: "hsl(var(--ink))", foreground: "hsl(var(--paper-raised))" },
        secondary: { DEFAULT: "hsl(var(--paper-sunk))", foreground: "hsl(var(--ink))" },
        muted: { DEFAULT: "hsl(var(--paper-sunk))", foreground: "hsl(var(--ink-3))" },
        destructive: { DEFAULT: "hsl(var(--critical))", foreground: "hsl(var(--paper-raised))" },
      },
      fontFamily: {
        // Swapped from Archivo — genuinely one of the most common
        // "default AI-template" heading fonts right now. Bricolage has
        // real character in its letterforms, still fully professional.
        display: ["'Bricolage Grotesque'", "ui-sans-serif", "system-ui", "sans-serif"],
        body: ["'Source Serif 4'", "Georgia", "ui-serif", "serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
        // Reserved for hero-scale (d1/d2) headlines only, not regular
        // body copy (Source Serif 4 stays the body-copy face
        // everywhere). Swapped from Fraunces to Instrument Serif to
        // match a specific wisprflow.ai reference screenshot — its
        // italic is genuinely elegant/calligraphic, which is the point:
        // it lets a hero headline mix upright + italic for emphasis
        // (`font-hero italic`), the way Wispr's own hero does.
        hero: ["'Instrument Serif'", "'Source Serif 4'", "Georgia", "ui-serif", "serif"],
      },
      fontSize: {
        label: ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.14em" }],
        micro: ["0.625rem", { lineHeight: "0.875rem", letterSpacing: "0.16em" }],
        d1: ["clamp(2.75rem, 7vw, 5.25rem)", { lineHeight: "0.94", letterSpacing: "-0.035em" }],
        d2: ["clamp(2rem, 4.4vw, 3.25rem)", { lineHeight: "1.02", letterSpacing: "-0.028em" }],
        d3: ["clamp(1.375rem, 2.2vw, 1.75rem)", { lineHeight: "1.15", letterSpacing: "-0.018em" }],
      },
      borderRadius: {
        // Tight tier — unchanged, for buttons/tags/inputs.
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.25rem",
        // NEW — soft tier, for section-level containers only
        // (persona cards, hero panels). Two-tier system per DESIGN.md.
        xl: "1.5rem",
        "2xl": "2.5rem",
      },
      boxShadow: {
        chart: "0 1px 0 0 hsl(var(--rule)), 0 12px 32px -24px hsl(var(--ink) / 0.5)",
        lift: "0 1px 0 0 hsl(var(--rule)), 0 20px 44px -28px hsl(var(--ink) / 0.55)",
        // NEW — hard, zero-blur "stamp" shadows for the verify-pass/
        // fail badge (M10/M5). Deliberately the opposite treatment
        // from `chart`/`lift`'s soft ambient blur — reads as a
        // physical stamp/sticker, not floating elevation.
        stamp: "3px 3px 0 0 hsl(var(--ink))",
        "stamp-pass": "3px 3px 0 0 hsl(var(--minor))",
        "stamp-fail": "3px 3px 0 0 hsl(var(--critical))",
      },
      keyframes: {
        sweep: { "0%": { transform: "translateX(-100%)" }, "100%": { transform: "translateX(300%)" } },
        "collapsible-down": { from: { height: "0" }, to: { height: "var(--radix-collapsible-content-height)" } },
        "collapsible-up": { from: { height: "var(--radix-collapsible-content-height)" }, to: { height: "0" } },
      },
      animation: {
        sweep: "sweep 1.6s cubic-bezier(0.4, 0, 0.2, 1) infinite",
        "collapsible-down": "collapsible-down 220ms cubic-bezier(0.2, 0, 0, 1)",
        "collapsible-up": "collapsible-up 180ms cubic-bezier(0.2, 0, 0, 1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
