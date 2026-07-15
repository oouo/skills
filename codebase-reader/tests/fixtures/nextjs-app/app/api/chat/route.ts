export const runtime = "edge";

export async function POST(request: Request): Promise<Response> {
  const input = (await request.json()) as { message?: string };
  if (!input.message) {
    return Response.json({ error: "message required" }, { status: 400 });
  }
  return Response.json({ reply: input.message.toUpperCase() });
}
