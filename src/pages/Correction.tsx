import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";

// M4 placeholder. M11 makes this deliberately the least-polished screen
// in the app (a simple panel/diagram, explicitly "planned for FYP-II")
// — this route existing now is just the scaffold that milestone fills.
export default function Correction() {
  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20">
        <p className="label-mono">M4 placeholder</p>
        <h1 className="mt-3 text-d1 font-hero">Correction / Learning</h1>
        <p className="mt-4 max-w-[58ch] text-ink-2">
          Real content lands in M11 — and should end up the least-polished screen
          in the app, deliberately.
        </p>
      </main>
      <Footer />
    </>
  );
}
