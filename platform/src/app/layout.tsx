import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Competitor Intel",
  description: "Short-form competitor content intelligence",
};

const NAV = [
  ["/", "Outlier Feed"],
  ["/matrix", "Pattern Matrix"],
  ["/search", "Semantic Search"],
  ["/remix", "Remix Studio"],
  ["/digests", "Weekly Digest"],
  ["/competitors", "Competitors"],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="sticky top-0 z-30 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur">
          <nav className="mx-auto flex max-w-[1600px] items-center gap-1 overflow-x-auto px-4 py-3 text-sm">
            <span className="mr-4 font-semibold tracking-tight text-white">◉ Competitor Intel</span>
            {NAV.map(([href, label]) => (
              <Link key={href} href={href} className="whitespace-nowrap rounded-md px-3 py-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white">
                {label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto max-w-[1600px] px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
