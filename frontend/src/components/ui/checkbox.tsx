"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

export interface CheckboxProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  onCheckedChange?: (checked: boolean) => void;
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, onCheckedChange, onChange, checked, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange?.(e);
      onCheckedChange?.(e.target.checked);
    };

    return (
      <label
        className={cn(
          "relative inline-flex h-4 w-4 shrink-0 cursor-pointer items-center justify-center rounded-sm border border-border",
          "transition-colors focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2",
          checked && "border-primary bg-primary",
          className
        )}
      >
        <input
          type="checkbox"
          ref={ref}
          checked={checked}
          onChange={handleChange}
          className="absolute inset-0 cursor-pointer opacity-0"
          {...props}
        />
        {checked && <Check className="h-3 w-3 text-primary-foreground" />}
      </label>
    );
  }
);
Checkbox.displayName = "Checkbox";

export { Checkbox };
