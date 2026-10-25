import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import type { CSSProperties } from "react";
import { school, themeVariables } from "@/config/school";
import { AppProviders } from "@/providers/app-providers";
import "./globals.css";

const body = Inter({ subsets: ["latin"], variable: "--font-body", display: "swap" });

export const metadata: Metadata = {
  title: { default: school.name, template: `%s · ${school.name}` },
  description: school.tagline,
  icons: { icon: school.favicon },
};

export const viewport: Viewport = { themeColor: school.theme.primary, width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-IN" className={`${body.variable}`} style={themeVariables() as CSSProperties}>
      <body className="min-h-screen bg-white">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:shadow"
        >
          Skip to content
        </a>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
