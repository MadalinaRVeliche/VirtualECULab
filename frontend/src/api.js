export const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export async function api(path, body, signal) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error(
      "Cannot reach the backend. Start both servers and check the API URL.",
    );
  }
  const data = await response.json();
  if (!response.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail.map((e) => `${e.loc?.join(".")}: ${e.msg}`).join("; ")
          : "Request failed.";
    throw new Error(detail);
  }
  return data;
}

export function hexBytes(text) {
  const parts = text.trim() ? text.trim().split(/\s+/) : [];
  if (parts.length > 8 || parts.some((part) => !/^[\da-f]{2}$/i.test(part))) {
    throw new Error("Use at most eight hexadecimal bytes, for example 10 27.");
  }
  return parts.map((part) => Number.parseInt(part, 16));
}
