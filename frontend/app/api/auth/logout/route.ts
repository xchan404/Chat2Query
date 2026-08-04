import { NextResponse } from "next/server";

export async function POST() {
  const response = NextResponse.json({ message: "Logged out successfully" });
  response.cookies.delete("c2q_access_token");
  response.cookies.delete("c2q_refresh_token");
  return response;
}
