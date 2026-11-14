import * as React from "react";
import * as SwitchPrimitives from "@radix-ui/react-switch";
import { cn } from "@/lib/utils";

const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitives.Root
    ref={ref}
    className={cn(
      "peer inline-flex h-[22px] w-[38px] shrink-0 cursor-pointer items-center rounded-full border border-ink/20 p-[2px]",
      "transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-50",
      "data-[state=checked]:border-ink data-[state=checked]:bg-ink data-[state=unchecked]:bg-paper-sunk",
      className,
    )}
    {...props}
  >
    <SwitchPrimitives.Thumb
      className={cn(
        "pointer-events-none block h-4 w-4 rounded-full shadow-sm ring-0",
        "transition-transform duration-200 ease-out",
        "data-[state=checked]:translate-x-4 data-[state=checked]:bg-paper-raised",
        "data-[state=unchecked]:translate-x-0 data-[state=unchecked]:bg-ink-3",
      )}
    />
  </SwitchPrimitives.Root>
));
Switch.displayName = SwitchPrimitives.Root.displayName;

export { Switch };
