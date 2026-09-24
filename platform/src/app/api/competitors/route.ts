import { NextResponse } from "next/server";
import { ACTORS, type Platform } from "@/lib/apify";
import { db, must } from "@/lib/db";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const { platform, handle, niche } = (await req.json()) as { platform?: Platform; handle?: string; niche?: string };
  if (!platform || !(platform in ACTORS) || !handle?.trim()) {
    return NextResponse.json({ error: "platform and handle required" }, { status: 400 });
  }
  const row = must(
    await db()
      .from("competitors")
      .upsert(
        { platform, handle: handle.trim().replace(/^@/, "").toLowerCase(), niche_category: niche || null, active: true },
        { onConflict: "platform,handle" },
      )
      .select()
      .single(),
    "add competitor",
  );
  return NextResponse.json(row);
}

export async function PATCH(req: Request) {
  const { id, active } = (await req.json()) as { id?: string; active?: boolean };
  if (!id || typeof active !== "boolean") return NextResponse.json({ error: "id and active required" }, { status: 400 });
  return NextResponse.json(must(await db().from("competitors").update({ active }).eq("id", id).select().single(), "update"));
}
