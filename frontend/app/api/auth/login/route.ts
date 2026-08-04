import { NextResponse } from "next/server";

const BACKEND_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const res = await fetch(`${BACKEND_API}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json(
        { detail: data.detail || "Authentication failed" },
        { status: res.status }
      );
    }

    const response = NextResponse.json(data);

    // Set httpOnly cookies for access_token and refresh_token
    if (data.access_token) {
      response.cookies.set({
        name: "c2q_access_token",
        value: data.access_token,
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: 30 * 60, // 30 minutes
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
        maxAge: 7 * 24 * 60 * 60, // 7 days
      });
    }

    return response;
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Internal Server Error";
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
