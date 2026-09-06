import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import { saveValidationCaseFile } from "@/core/validation/validationCaseFileStore";
import { GET } from "./route";

describe("GET /api/validation-cases", () => {
  const originalDataDir = process.env.CAREERDIFF_DATA_DIR;
  let directory: string;

  beforeEach(async () => {
    directory = await mkdtemp(path.join(tmpdir(), "careerdiff-validation-cases-route-"));
    process.env.CAREERDIFF_DATA_DIR = directory;
  });

  afterEach(async () => {
    if (originalDataDir === undefined) delete process.env.CAREERDIFF_DATA_DIR;
    else process.env.CAREERDIFF_DATA_DIR = originalDataDir;
    await rm(directory, { recursive: true, force: true });
  });

  it("returns every persisted case, not just what one browser's localStorage happens to hold", async () => {
    await saveValidationCaseFile({
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      jobDescription: "job description text over thirty characters long",
      candidateProfile: "candidate profile text over thirty characters long",
      result: mockAnalysisResult,
    });
    await saveValidationCaseFile({
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      jobDescription: "second job description text over thirty characters",
      candidateProfile: "second candidate profile text over thirty characters",
      result: mockAnalysisResult,
    });

    const response = await GET();
    const body = (await response.json()) as { cases: unknown[] };

    expect(response.status).toBe(200);
    expect(body.cases).toHaveLength(2);
  });
});
