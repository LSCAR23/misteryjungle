import { forwardRef, type InputHTMLAttributes } from "react";
import { Check } from "lucide-react";
import { cn } from "./cn";

export const Checkbox = forwardRef<HTMLInputElement, Omit<InputHTMLAttributes<HTMLInputElement>, "type">>(
  function Checkbox({ className, ...props }, ref) {
    return (
      <span className={cn("relative inline-flex size-7 shrink-0", className)}>
        <input ref={ref} type="checkbox" className="peer absolute inset-0 z-10 m-0 size-full cursor-pointer opacity-0" {...props} />
        <span
          aria-hidden="true"
          className="flex size-7 items-center justify-center rounded-lg border-2 border-border bg-bg text-transparent transition-colors duration-150 peer-checked:border-red peer-checked:bg-red peer-checked:text-white peer-focus-visible:ring-2 peer-focus-visible:ring-red peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-bg peer-disabled:opacity-50"
        >
          <Check className="size-5" strokeWidth={3} />
        </span>
      </span>
    );
  },
);
