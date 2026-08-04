import { NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const cookieStore = await cookies();
    let refreshToken = cookieStore.get("c2q_refresh_token")?.value;

    // Fallback: check if client provided refresh_token in request body
    if (!refreshToken) {
      try {
        const body = await request.json();
        refreshToken = body.refresh_token;
      } catch {
        /* body empty */
      }
    }

    if (!refreshToken) {
      return NextResponse.json({ detail: "Refresh token missing" }, { status: 401 });
    }

    const res = await fetch(`${BACKEND_API}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const data = await res.json();

    if (!res.ok) {
      const response = NextResponse.json(
        { detail: data.detail || "Refresh failed" },
        { status: res.status }
      );
      // Clear invalid cookies
      response.cookies.delete("c2q_access_token");
      response.cookies.delete("c2q_refresh_token");
      return response;
    }

    const response = NextResponse.json(data);

    // Set updated httpOnly cookies
    if (data.access_token) {
      response.cookies.set({
        name: "c2q_access_token",
        value: data.access_token,
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: 30 * 60,
      });
    }

    if (data.refresh_token) {
      response.cookies.set({
        name: "c2q_refresh_token",
        value: data.refresh_token,
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: 7 * 24 * 60 * 60,
      });
    }

    return response;
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Internal Server Error";
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
