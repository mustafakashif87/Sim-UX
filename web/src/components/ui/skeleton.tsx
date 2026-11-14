import * as React from "react";
import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("relative overflow-hidden rounded-md bg-paper-sunk", className)} {...props}>
      {/* A scan passing over the well, not a pulse. Matches the running
          state's own honesty principle — motion that says "reading", not
          "loading 40%". */}
      <div className="absolute inset-y-0 w-1/3 animate-sweep bg-gradient-to-r from-transparent via-paper-raised/80 to-transparent" />
    </div>
  );
}

export { Skeleton };
