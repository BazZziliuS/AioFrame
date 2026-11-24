import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, errorCode, request } from "./client";

vi.mock("@/shared/telegram/sdk", () => ({ getRawInitData: () => "query_id=1&hash=abc" }));

function mockFetch(response: Response | Error) {
  const fetchMock = vi.fn(() =>
    response instanceof Error ? Promise.reject(response) : Promise.resolve(response),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("request", () => {
  it("sends initData and JSON body, returns parsed JSON", async () => {
    const fetchMock = mockFetch(Response.json({ ok: true }));

    await expect(request("POST", "/api/feedback", { body: { text: "hi" } })).resolves.toEqual({
      ok: true,
    });

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/feedback");
    expect(init.headers).toMatchObject({
      Authorization: "tma query_id=1&hash=abc",
      "Content-Type": "application/json",
    });
    expect(init.body).toBe(JSON.stringify({ text: "hi" }));
  });

  it("turns API errors into ApiError with the error code", async () => {
    mockFetch(Response.json({ detail: "maintenance" }, { status: 503 }));

    const error = await request("GET", "/api/me").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 503, detail: "maintenance" });
  });

  it("uses a generic code when the error body is not JSON", async () => {
    mockFetch(new Response("Bad Gateway", { status: 502 }));
    await expect(request("GET", "/api/me")).rejects.toMatchObject({ detail: "server_error" });
  });

  it("reports network failures with status 0", async () => {
    mockFetch(new TypeError("Failed to fetch"));
    await expect(request("GET", "/api/me")).rejects.toMatchObject({
      status: 0,
      detail: "network_error",
    });
  });
});

describe("errorCode", () => {
  it("returns the API code or a generic one", () => {
    expect(errorCode(new ApiError(403, "banned"))).toBe("banned");
    expect(errorCode(new Error("boom"))).toBe("server_error");
  });
});
