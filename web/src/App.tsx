import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import Landing from "@/pages/Landing";
import NewRun from "@/pages/NewRun";
import LiveRun from "@/pages/LiveRun";
import Running from "@/pages/Running";
import Results from "@/pages/Results";
import FindingDetail from "@/pages/FindingDetail";
import Correction from "@/pages/Correction";
import Tokens from "@/pages/dev/Tokens";
import Fixture from "@/pages/dev/Fixture";
import Metaphors from "@/pages/dev/Metaphors";

/** Ported from site-doctor as-is: router doesn't handle hash targets or
 *  restore scroll on navigation, so do both here. */
function ScrollBehaviour() {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (hash) {
      const target = document.querySelector(hash);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
    }
    window.scrollTo({ top: 0 });
  }, [pathname, hash]);

  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollBehaviour />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/new-run" element={<NewRun />} />
        <Route path="/runs/:runId" element={<LiveRun />} />
        <Route path="/running" element={<Running />} />
        <Route path="/results" element={<Results />} />
        <Route path="/results/:findingId" element={<FindingDetail />} />
        <Route path="/correction" element={<Correction />} />

        {/* Dev-only verification pages from M1-M3 — never linked from
            SiteNav/Footer, excluded from prod by the import.meta.env.DEV
            guard. Must be gone (or confirmed still gated) by M12. */}
        {import.meta.env.DEV && <Route path="/dev/tokens" element={<Tokens />} />}
        {import.meta.env.DEV && <Route path="/dev/fixture" element={<Fixture />} />}
        {import.meta.env.DEV && <Route path="/dev/metaphors" element={<Metaphors />} />}

        {/* Anything else is a mistyped URL; the landing page is the
            safest place to put someone who is lost. */}
        <Route path="*" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  );
}
