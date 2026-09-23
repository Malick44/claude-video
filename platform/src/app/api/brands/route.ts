import { NextResponse } from "next/server";
import { db, must } from "@/lib/db";

export const runtime = "nodejs";

export async function GET() {
  return NextResponse.json(must(await db().from("brand_profiles").select("id, name, context").order("created_at"), "brands"));
}

export async function POST(req: Request) {
  const { name, context } = (await req.json()) as { name?: string; context?: string };
  if (!name?.trim() || !context?.trim()) return NextResponse.json({ error: "name and context required" }, { status: 400 });
  return NextResponse.json(must(await db().from("brand_profiles").insert({ name, context }).select().single(), "create brand"));
}
