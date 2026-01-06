import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "success";
  size?: "sm" | "md" | "lg";
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, disabled, ...props }, ref) => {
    const baseStyles =
      "relative inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden group";

    const variants = {
      primary: "bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 text-white hover:shadow-xl hover:shadow-blue-500/50 hover:scale-105 focus:ring-blue-500 shadow-lg",
      secondary: "bg-gradient-to-r from-green-500 via-green-600 to-green-700 text-white hover:shadow-xl hover:shadow-green-500/50 hover:scale-105 focus:ring-green-500 shadow-lg",
      outline: "border-2 border-blue-500 text-blue-600 hover:bg-blue-50 hover:border-blue-600 focus:ring-blue-400 backdrop-blur-sm",
      ghost: "text-slate-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-green-50 focus:ring-slate-400",
      danger: "bg-gradient-to-r from-red-500 via-red-600 to-red-700 text-white hover:shadow-xl hover:shadow-red-500/50 hover:scale-105 focus:ring-red-500 shadow-lg",
      success: "bg-gradient-to-r from-green-500 via-green-600 to-green-700 text-white hover:shadow-xl hover:shadow-green-500/50 hover:scale-105 focus:ring-green-500 shadow-lg",
    };

    const sizes = {
      sm: "px-4 py-2 text-sm",
      md: "px-6 py-3 text-base",
      lg: "px-8 py-4 text-lg",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled}
        {...props}
      >
        <span className="relative z-10 flex items-center gap-2">{children}</span>
        {(variant === "primary" || variant === "secondary" || variant === "danger" || variant === "success") && (
          <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button };
