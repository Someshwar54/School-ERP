import { NextResponse, type NextRequest } from "next/server";
import { env } from "@/config/env";
import { LOGIN_PATH } from "@/services/auth";

/**
 * UX-only guard: sends visitors without a session cookie to the right sign-in page.
 * It does NOT authorise anything — every API call is checked by the backend.
 */

export function proxy(request: NextRequest) {
  const workspace = request.nextUrl.pathname.split("/")[2];
  if (!request.cookies.has(env.sessionCookieName) && workspace in LOGIN_PATH) {
    return NextResponse.redirect(new URL(LOGIN_PATH[workspace as keyof typeof LOGIN_PATH], request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/erp/student/:path*", "/erp/staff/:path*", "/erp/management/:path*"] };
