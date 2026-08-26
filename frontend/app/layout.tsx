import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CyberSOS — I've been scammed. What do I do now?",
  description:
    "CyberSOS helps you take the right immediate steps after a cyber or financial fraud incident, organize your evidence, and reach the official cybercrime reporting channels.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
