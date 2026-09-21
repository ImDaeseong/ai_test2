import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { loadSharedOpenAiKey } from "./loadSharedOpenAiKey";

const originalKey = process.env.OPENAI_API_KEY;

afterEach(() => {
  if (originalKey === undefined) delete process.env.OPENAI_API_KEY;
  else process.env.OPENAI_API_KEY = originalKey;
});

describe("loadSharedOpenAiKey", () => {
  it("loads only OPENAI_API_KEY without returning its value", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "careerdiff-key-"));
    const file = path.join(dir, "keys.env");
    fs.writeFileSync(file, "OTHER_KEY=do-not-load\nOPENAI_API_KEY=test-secret\n", "utf8");
    delete process.env.OPENAI_API_KEY;
    delete process.env.OTHER_KEY;

    expect(loadSharedOpenAiKey(file)).toBe(true);
    expect(process.env.OPENAI_API_KEY).toBe("test-secret");
    expect(process.env.OTHER_KEY).toBeUndefined();
    fs.rmSync(dir, { recursive: true, force: true });
  });

  it("returns false when the credential file is unavailable", () => {
    delete process.env.OPENAI_API_KEY;
    expect(loadSharedOpenAiKey(path.join(os.tmpdir(), "missing-careerdiff-keys.env"))).toBe(false);
  });
});
