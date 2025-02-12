import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart Gateway",
  description: "Smart Gateway UI for managing ORBCOMM ISAT and OGx protocols",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  )
}
