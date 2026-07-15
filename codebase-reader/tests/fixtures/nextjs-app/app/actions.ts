"use server";

export async function savePreference(value: string): Promise<{ value: string }> {
  if (!value) {
    throw new Error("value is required");
  }
  return { value };
}
