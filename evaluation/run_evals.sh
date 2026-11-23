#!/usr/bin/env bash
# Run evaluations to completion, waiting out spent API quotas.
#
#   bash evaluation/run_evals.sh                  # from the repo root
#   PY=.venv/Scripts/python OUT=../eval-runs bash evaluation/run_evals.sh
#
# Each pass gives every unfinished evaluation one go. agent.evaluate switches
# keys itself (LLM_API_KEY, LLM_API_KEY_2 ... in .env) and keeps each output
# folder on one model. When a pass is blocked by quota, wait 11 minutes and
# try again; stop when every evaluation reports "0 to run". A lock stops a
# second copy from running at the same time.
#
# Spec: persona|output folder|extra arguments. P2 and P3 get the full 5-seed
# protocol; P4 to P14 get a smoke run (1 seed, buggy and clean pages).
cd "$(dirname "$0")/.." || exit 1
PY="${PY:-python}"
OUT="${OUT:-eval-runs}"
mkdir -p "$OUT"
LOCK="$OUT/run_evals.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "another run_evals.sh is already running (remove $LOCK if not)"; exit 1
fi
trap 'rmdir "$LOCK"' EXIT

FULL="--seeds 5"
SMOKE="--seeds 1 --conditions persona_buggy,persona_clean"
EVALS=(
  "memoryless|p2-eval|$FULL"
  "low_literacy|p3-eval|$FULL"
)
for p in screen_reader keyboard_only touch_imprecise low_vision_zoom skimmer \
         interrupted slow_network help_seeker habitual power_user older_adult; do
  EVALS+=("$p|smoke-$p|$SMOKE")
done

for pass in $(seq 1 80); do
  pending=0
  for spec in "${EVALS[@]}"; do
    IFS='|' read -r persona out args <<< "$spec"
    log="$OUT/$out.attempt.log"
    # $args is unquoted on purpose: it holds several arguments.
    PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 "$PY" -m agent.evaluate --persona "$persona" \
      $args --out "$OUT/$out" > "$log" 2>&1
    echo "pass $pass $persona: $(head -1 "$log")"
    if ! head -1 "$log" | grep -q " 0 to run"; then pending=$((pending + 1)); fi
  done
  if [ "$pending" -eq 0 ]; then echo "all evaluations finished"; exit 0; fi
  sleep 660
done
