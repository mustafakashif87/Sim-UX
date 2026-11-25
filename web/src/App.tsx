import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import Landing from "@/pages/Landing";
import NewRun from "@/pages/NewRun";
import LiveRun from "@/pages/LiveRun";
import Results from "@/pages/Results";

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
        <Route path="/results" element={<Results />} />

        {/* Anything else is a mistyped URL; the landing page is the
            safest place to put someone who is lost. */}
        <Route path="*" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  );
}
