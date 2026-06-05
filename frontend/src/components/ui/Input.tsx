"use client";
import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, ...props }, ref) => (
    <div className="w-full">
      {label && <label className="block text-sm font-medium text-muted mb-1.5">{label}</label>}
      <input
        ref={ref}
        className={cn(
          "w-full px-3.5 py-2.5 bg-surface-1 border rounded-xl text-sm text-fg placeholder:text-muted",
          "focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30",
          "transition-all duration-200",
          error ? "border-danger" : "border-border",
          className,
        )}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  ),
);
Input.displayName = "Input";
export default Input;
