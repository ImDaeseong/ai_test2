import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import { listValidationCaseFiles, validationDataDirectory } from "./validationCaseFileStore";

describe("validationDataDirectory", () => {
  const original = process.env.CAREERDIFF_DATA_DIR;

  afterEach(() => {
    if (original === undefined) delete process.env.CAREERDIFF_DATA_DIR;
    else process.env.CAREERDIFF_DATA_DIR = original;
  });

  it("defaults to the sibling data folder when no override is set", () => {
    delete process.env.CAREERDIFF_DATA_DIR;
    expect(validationDataDirectory().endsWith(`${path.sep}data`)).toBe(true);
  });

  it("honors CAREERDIFF_DATA_DIR so tests and E2E never touch the real data folder", () => {
    const isolated = path.join(process.cwd(), "tmp-test-data");
    process.env.CAREERDIFF_DATA_DIR = isolated;
    expect(validationDataDirectory()).toBe(path.resolve(isolated));
  });
});

describe("listValidationCaseFiles", () => {
  const originalDataDir = process.env.CAREERDIFF_DATA_DIR;
  let directory: string;

  beforeEach(async () => {
    directory = await mkdtemp(path.join(tmpdir(), "careerdiff-validation-cases-"));
    process.env.CAREERDIFF_DATA_DIR = directory;
  });

  afterEach(async () => {
    if (originalDataDir === undefined) delete process.env.CAREERDIFF_DATA_DIR;
    else process.env.CAREERDIFF_DATA_DIR = originalDataDir;
    await rm(directory, { recursive: true, force: true });
  });

  it("returns an empty list when the data folder does not exist yet", async () => {
    await rm(directory, { recursive: true, force: true });
    expect(await listValidationCaseFiles()).toEqual([]);
  });

  it("reads every valid case file, sorted by createdAt, and skips malformed or schema-invalid files", async () => {
    const older = {
      id: crypto.randomUUID(),
      createdAt: "2026-01-01T00:00:00.000Z",
      jobDescription: "older job description text over thirty chars",
      candidateProfile: "older candidate profile text over thirty chars",
      result: mockAnalysisResult,
    };
    const newer = {
      id: crypto.randomUUID(),
      createdAt: "2026-02-01T00:00:00.000Z",
      jobDescription: "newer job description text over thirty chars",
      candidateProfile: "newer candidate profile text over thirty chars",
      result: mockAnalysisResult,
    };
    await mkdir(directory, { recursive: true });
    // Written out of chronological order to prove the function sorts, not just returns as-is.
    await writeFile(path.join(directory, `${newer.id}.json`), JSON.stringify(newer), "utf8");
    await writeFile(path.join(directory, `${older.id}.json`), JSON.stringify(older), "utf8");
    await writeFile(path.join(directory, "corrupted.json"), "not json", "utf8");
    await writeFile(
      path.join(directory, "stale-schema.json"),
      JSON.stringify({ ...older, id: crypto.randomUUID(), result: { fitScore: older.result.fitScore } }),
      "utf8",
    );
    await writeFile(path.join(directory, "readme.txt"), "not a case file", "utf8");

    const result = await listValidationCaseFiles();

    expect(result.map((c) => c.id)).toEqual([older.id, newer.id]);
  });

  it("recovers a legacy file saved before relatedSkillGuidance existed, defaulting it to []", async () => {
    const legacyResult: Record<string, unknown> = { ...mockAnalysisResult };
    delete legacyResult.relatedSkillGuidance;
    const legacyCase = {
      id: crypto.randomUUID(),
      createdAt: "2025-12-01T00:00:00.000Z",
      jobDescription: "legacy job description text over thirty chars",
      candidateProfile: "legacy candidate profile text over thirty chars",
      result: legacyResult,
    };
    await mkdir(directory, { recursive: true });
    await writeFile(path.join(directory, `${legacyCase.id}.json`), JSON.stringify(legacyCase), "utf8");

    const result = await listValidationCaseFiles();

    expect(result).toHaveLength(1);
    expect(result[0].result.relatedSkillGuidance).toEqual([]);
  });
});
