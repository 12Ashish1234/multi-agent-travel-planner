import "./globals.css";

export const metadata = {
  title: "AI Trip Planner",
  description: "Intelligent multi-agent itinerary planner",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
