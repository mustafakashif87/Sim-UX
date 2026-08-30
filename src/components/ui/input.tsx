import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        // Inputs are wells sunk into the chart stock, and everything typed
        // into them is data — hence mono.
        "flex h-12 w-full rounded-md border border-rule bg-paper-sunk px-3.5 font-mono text-sm text-ink",
        "transition-colors duration-200 placeholder:text-ink-3/70",
        "hover:border-ink/30 focus:border-ink focus:bg-paper-raised focus:outline-none",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };
