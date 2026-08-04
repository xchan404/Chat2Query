import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get("c2q_access_token")?.value;

  const isAuthRoute = pathname.startsWith("/login");
  const isProtectedRoute =
    pathname.startsWith("/chat") ||
    pathname.startsWith("/connections") ||
    pathname.startsWith("/knowledge") ||
    pathname.startsWith("/permissions") ||
    pathname.startsWith("/audit");

  // Unauthenticated user trying to access protected route -> redirect to /login
  if (isProtectedRoute && !accessToken) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  // Authenticated user trying to access /login -> redirect to /chat
  if (isAuthRoute && accessToken) {
    const chatUrl = new URL("/chat", request.url);
    return NextResponse.redirect(chatUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/chat/:path*",
    "/connections/:path*",
    "/knowledge/:path*",
    "/permissions/:path*",
    "/audit/:path*",
  ],
};
