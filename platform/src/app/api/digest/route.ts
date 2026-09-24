import { NextResponse } from "next/server";
import { inngest } from "@/inngest/client";

export async function POST() {
  await inngest.send({ name: "digest/generate.requested", data: {} });
  return NextResponse.json({ queued: true }, { status: 202 });
}
