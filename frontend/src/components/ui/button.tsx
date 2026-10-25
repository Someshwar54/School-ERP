import Link from "next/link";
import type { ButtonHTMLAttributes, ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "accent" | "inverse" | "outline-inverse";
type Size = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-all disabled:cursor-not-allowed disabled:opacity-60 whitespace-nowrap";
const variants: Record<Variant, string> = {
  primary: "bg-brand text-brand-contrast shadow-sm hover:bg-brand-strong hover:shadow-md",
  accent: "bg-brand text-brand-contrast shadow-sm hover:bg-brand-strong hover:shadow-md",
  secondary: "border-2 border-ink bg-white text-ink hover:bg-ink hover:text-white",
  inverse: "bg-white text-brand shadow-sm hover:bg-brand-soft",
  "outline-inverse": "border-2 border-white/70 text-white hover:bg-white hover:text-ink",
  ghost: "text-brand hover:bg-brand-soft",
  danger: "bg-red-700 text-white hover:bg-red-800",
};
const sizes: Record<Size, string> = { sm: "h-8 px-4 text-sm", md: "h-10 px-5 text-sm", lg: "h-12 px-8 text-base" };

export function buttonClasses(variant: Variant = "primary", size: Size = "md", className?: string): string {
  return cn(base, variants[variant], sizes[size], className);
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({ variant = "primary", size = "md", loading, icon, className, children, disabled, ...rest }: ButtonProps) {
  return (
    <button className={buttonClasses(variant, size, className)} disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {loading ? <span className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent" aria-hidden /> : icon}
      {children}
    </button>
  );
}

export function ButtonLink({
  variant = "primary",
  size = "md",
  className,
  ...rest
}: ComponentProps<typeof Link> & { variant?: Variant; size?: Size }) {
  return <Link className={buttonClasses(variant, size, className)} {...rest} />;
}
