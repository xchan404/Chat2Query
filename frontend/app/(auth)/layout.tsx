/**
 * Auth route group layout — no AppShell, just the root providers.
 * Login is full-page; it doesn't use the Sidebar/TopBar chrome.
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
