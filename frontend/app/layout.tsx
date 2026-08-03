import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/AuthProvider";

export const metadata: Metadata = {
  title: "Chat2Query // Enterprise Data Audit & Control Room",
  description: "Multi-Tenant Text-to-SQL & Document Chat Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-paper text-ink-dark">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
