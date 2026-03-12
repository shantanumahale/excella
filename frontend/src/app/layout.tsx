import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { ThemeProvider } from "@/providers/theme-provider";
import { AuthProvider } from "@/providers/auth-provider";
import { Navbar } from "@/components/layout/navbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Excella - Financial Screener",
  description:
    "Screen, compare, and analyze financial data across public companies.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider defaultTheme="system">
          <QueryProvider>
            <AuthProvider>
              <div className="relative flex min-h-screen flex-col">
                <Navbar />
                <main className="flex-1">
                  <div className="mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 lg:px-8">
                    {children}
                  </div>
                </main>
              </div>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
