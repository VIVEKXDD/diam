import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Diamind — Diamond Intelligence",
  description: "AI-powered diamond inventory and market intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}