import { describe, expect, it } from "vitest";
import { BodyTooLargeError, readJsonLimited } from "./readJsonLimited";

function post(body: BodyInit, headers: Record<string, string> = {}): Request {
  return new Request("http://localhost/api/x", { method: "POST", body, headers });
}

describe("readJsonLimited", () => {
  it("parses a body within the limit", async () => {
    await expect(readJsonLimited(post(JSON.stringify({ a: 1 })), 100)).resolves.toEqual({ a: 1 });
  });

  it("rejects a body whose declared length exceeds the limit", async () => {
    const request = post("{}", { "content-length": "5000" });
    await expect(readJsonLimited(request, 100)).rejects.toBeInstanceOf(BodyTooLargeError);
  });

  it("rejects an oversized body even when the declared length is missing or wrong", async () => {
    const big = JSON.stringify({ text: "x".repeat(500) });
    await expect(readJsonLimited(post(big, { "content-length": "abc" }), 100)).rejects.toBeInstanceOf(BodyTooLargeError);
    await expect(readJsonLimited(post(big, { "content-length": "2" }), 100)).rejects.toBeInstanceOf(BodyTooLargeError);
  });

  it("counts a streamed body that sends no Content-Length", async () => {
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        const chunk = new TextEncoder().encode("x".repeat(60));
        controller.enqueue(chunk);
        controller.enqueue(chunk);
        controller.close();
      },
    });
    const request = new Request("http://localhost/api/x", {
      method: "POST",
      body: stream,
      duplex: "half",
    } as RequestInit);
    await expect(readJsonLimited(request, 100)).rejects.toBeInstanceOf(BodyTooLargeError);
  });

  it("still reports invalid JSON as a SyntaxError", async () => {
    await expect(readJsonLimited(post("not json"), 100)).rejects.toBeInstanceOf(SyntaxError);
  });
});
