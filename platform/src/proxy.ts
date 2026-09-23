// Optional HTTP basic auth for the dashboard. Webhooks and the Inngest endpoint
// authenticate themselves (shared secret / Inngest signing key) and are excluded.
import { NextResponse, type NextRequest } from "next/server";

export function proxy(req: NextRequest) {
  const password = process.env.DASHBOARD_PASSWORD;
  if (!password) return NextResponse.next();
  const header = req.headers.get("authorization") ?? "";
  const [scheme, encoded] = header.split(" ");
  if (scheme === "Basic" && encoded) {
    const [, pass] = atob(encoded).split(":");
    if (pass === password) return NextResponse.next();
  }
  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="competitor-intel"' },
  });
}

export const config = {
  matcher: ["/((?!api/inngest|api/webhooks|_next/static|_next/image|favicon.ico).*)"],
};
