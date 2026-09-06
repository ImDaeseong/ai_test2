import { mkdir, mkdtemp, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mockAnalysisResult } from "@/core/mocks/mockAnalysisResult";
import { listValidationCaseFiles, saveValidationCaseFile, validationDataDirectory } from "./validationCaseFileStore";

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

describe("saveValidationCaseFile (candidate-profile dedup)", () => {
  const originalDataDir = process.env.CAREERDIFF_DATA_DIR;
  let directory: string;

  beforeEach(async () => {
    directory = await mkdtemp(path.join(tmpdir(), "careerdiff-validation-cases-save-"));
    process.env.CAREERDIFF_DATA_DIR = directory;
  });

  afterEach(async () => {
    if (originalDataDir === undefined) delete process.env.CAREERDIFF_DATA_DIR;
    else process.env.CAREERDIFF_DATA_DIR = originalDataDir;
    await rm(directory, { recursive: true, force: true });
  });

  it("stores the profile text once under data/profiles/<hash>.json instead of embedding it per case", async () => {
    const sharedProfile = "shared candidate profile text repeated across many cases, over 30 chars";
    await saveValidationCaseFile({
      id: crypto.randomUUID(),
      createdAt: "2026-01-01T00:00:00.000Z",
      jobDescription: "first job description text over thirty characters",
      candidateProfile: sharedProfile,
      result: mockAnalysisResult,
    });
    await saveValidationCaseFile({
      id: crypto.randomUUID(),
      createdAt: "2026-01-02T00:00:00.000Z",
      jobDescription: "second job description text over thirty characters",
      candidateProfile: sharedProfile,
      result: mockAnalysisResult,
    });

    const caseEntries = (await readdir(directory)).filter((entry) => entry.endsWith(".json"));
    expect(caseEntries).toHaveLength(2);
    for (const entry of caseEntries) {
      const raw = JSON.parse(await readFile(path.join(directory, entry), "utf8")) as Record<string, unknown>;
      expect(raw.candidateProfile).toBeUndefined();
      expect(typeof raw.candidateProfileHash).toBe("string");
    }

    const profileEntries = await readdir(path.join(directory, "profiles"));
    expect(profileEntries).toHaveLength(1);
  });

  it("round-trips through listValidationCaseFiles with the original candidateProfile text intact", async () => {
    const original = "candidate profile text that must survive the hash round-trip, over 30 chars";
    await saveValidationCaseFile({
      id: crypto.randomUUID(),
      createdAt: "2026-01-01T00:00:00.000Z",
      jobDescription: "job description text over thirty characters long",
      candidateProfile: original,
      result: mockAnalysisResult,
    });

    const [loaded] = await listValidationCaseFiles();
    expect(loaded.candidateProfile).toBe(original);
  });

  it("skips a case whose referenced profile file is missing, rather than failing the whole listing", async () => {
    await mkdir(directory, { recursive: true });
    await writeFile(
      path.join(directory, `${crypto.randomUUID()}.json`),
      JSON.stringify({
        id: crypto.randomUUID(),
        createdAt: "2026-01-01T00:00:00.000Z",
        jobDescription: "job description text over thirty characters long",
        candidateProfileHash: "0000000000000000000000000000000000000000000000000000000000000000",
        result: mockAnalysisResult,
      }),
      "utf8",
    );

    expect(await listValidationCaseFiles()).toEqual([]);
  });
});
