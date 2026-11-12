// Local development uses FastAPI on port 8000. The hosted build sets
// VITE_API_URL to an empty string so requests go to the frontend's origin.
// Use ?? to preserve that empty string and fall back only if it is unset.
export const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export async function api(path, body, signal) {
  let response;
  try {
    // Callers omit the body for reads and pass a JSON body for POST requests.
    response = await fetch(`${API_URL}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (error) {
    // A component may cancel a request during cleanup. Preserve AbortError
    // so the caller can distinguish cancellation from a connection failure.
    if (error.name === "AbortError") throw error;
    throw new Error(
      "Cannot reach the backend. Start both servers and check the API URL.",
    );
  }

  const data = await response.json();
  if (!response.ok) {
    // FastAPI can return a single error message or a list of validation
    // errors. Include the field path so the user can locate invalid input.
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
  // A blank input represents an empty payload. Otherwise, require one
  // two-digit hex token per byte and at most eight bytes for Classical CAN.
  const parts = text.trim() ? text.trim().split(/\s+/) : [];
  if (parts.length > 8 || parts.some((part) => !/^[\da-f]{2}$/i.test(part))) {
    throw new Error("Use at most eight hexadecimal bytes, for example 10 27.");
  }
  return parts.map((part) => Number.parseInt(part, 16));
}
