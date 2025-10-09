import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Microrrede · Dashboard",
  description: "Otimização inteligente de microrrede em tempo real",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="antialiased">{children}</body>
    </html>
  );
}