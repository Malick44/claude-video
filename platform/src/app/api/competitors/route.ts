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
  const { id, active, handle, platform, niche } = (await req.json()) as {
    id?: string;
    active?: boolean;
    handle?: string;
    platform?: Platform;
    niche?: string;
  };
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });

  const updates: Record<string, unknown> = {};
  if (typeof active === "boolean") updates.active = active;
  if (handle !== undefined) {
    const cleanHandle = handle.trim().replace(/^@/, "").toLowerCase();
    if (!cleanHandle) return NextResponse.json({ error: "handle cannot be empty" }, { status: 400 });
    updates.handle = cleanHandle;
  }
  if (platform !== undefined) {
    if (!(platform in ACTORS)) return NextResponse.json({ error: "invalid platform" }, { status: 400 });
    updates.platform = platform;
  }
  if (niche !== undefined) {
    updates.niche_category = niche.trim() || null;
  }

  const row = must(
    await db().from("competitors").update(updates).eq("id", id).select().single(),
    "update competitor",
  );
  return NextResponse.json(row);
}

export async function DELETE(req: Request) {
  const { searchParams } = new URL(req.url);
  let id = searchParams.get("id");
  if (!id) {
    try {
      const body = (await req.json()) as { id?: string };
      id = body?.id ?? null;
    } catch {
      // ignore
    }
  }
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });

  await db().from("competitors").delete().eq("id", id);
  return NextResponse.json({ ok: true, id });
}
