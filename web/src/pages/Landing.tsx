import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { Hero } from "@/components/landing/Hero";
import { GroundedInStandards } from "@/components/landing/GroundedInStandards";
import { PersonaShowcase } from "@/components/landing/PersonaShowcase";
import { Comparison } from "@/components/landing/Comparison";
import { PipelineStages } from "@/components/landing/PipelineStages";
import { ConcernCloud } from "@/components/landing/ConcernCloud";
import { CapabilityGrid } from "@/components/landing/CapabilityGrid";
import { FinalCta } from "@/components/landing/FinalCta";

// M6b — landing v2, redesigned against a reference of wisprflow.ai's
// actual marketing page. Section order: hero (now with a real toggle)
// -> grounded-in-standards strip -> persona cards -> honest comparison
// -> pipeline stages -> concern cloud -> capability grid -> closing CTA.
// See the milestone plan's M6b entry for the full mapping and the three
// integrity decisions (no fabricated customers, no testimonials, a real
// interactive hero toggle) that shaped it.
export default function Landing() {
  return (
    <>
      <SiteNav variant="landing" />
      <main>
        <Hero />
        <GroundedInStandards />
        <PersonaShowcase />
        <Comparison />
        <PipelineStages />
        <ConcernCloud />
        <CapabilityGrid />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}
