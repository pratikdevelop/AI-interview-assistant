import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProofPath AI — Career evidence, not guesses",
  description: "Map job requirements to evidence in your resume and project repository, then get a focused preparation plan.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
