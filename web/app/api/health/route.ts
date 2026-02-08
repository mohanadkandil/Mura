import { NextResponse } from "next/server";

const API_BASE = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      return NextResponse.json({ error: "Backend not available" }, { status: 503 });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Backend not available" }, { status: 503 });
  }
}
