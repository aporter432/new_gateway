import type { Metadata } from "next";
import { Montserrat, Playfair_Display, Poppins, Roboto } from "next/font/google";
import "./globals.css";
import "./typography.css";

// Configure fonts
const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-poppins",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
});

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat",
});

const roboto = Roboto({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-roboto",
});

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
    <html lang="en" className={`${poppins.variable} ${playfair.variable} ${montserrat.variable} ${roboto.variable}`}>
      <body>{children}</body>
    </html>
  )
}
