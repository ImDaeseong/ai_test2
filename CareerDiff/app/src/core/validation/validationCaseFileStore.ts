import { link, mkdir, open, readdir, readFile, unlink } from "node:fs/promises";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { backfillLegacyAnalysisResult } from "@/core/schemas/analysisResult";
import type { AnalysisValidationCase } from "@/core/validation/analysisValidationStore";
import { analysisValidationCaseSchema } from "@/core/validation/validationCaseSchema";

export function validationDataDirectory(): string {
  // Tests and E2E point this at a throwaway directory so they never write
  // into the real CareerDiff/data folder (see playwright.config.ts).
  const override = process.env.CAREERDIFF_DATA_DIR;
  if (override) return path.resolve(override);
  // turbopackIgnore: process.cwd() is dynamic to Next's file tracer, which
  // otherwise falls back to tracing the whole project (including data/*.json,
  // which holds candidate PII) as a build-time NFT warning.
  return path.resolve(/* turbopackIgnore: true */ process.cwd(), "..", "data");
}

/**
 * Candidate profiles repeat verbatim across many validation cases (the same
 * resume analyzed against many job postings), so cases reference the profile
 * text by content hash instead of embedding it -- see docs/ARCHITECTURE.md.
 */
function profilesDirectory(directory: string): string {
  return path.join(directory, "profiles");
}

function profileHash(candidateProfile: string): string {
  return createHash("sha256").update(candidateProfile, "utf8").digest("hex");
}

async function writeFileAtomic(destination: string, content: string): Promise<{ created: boolean }> {
  const directory = path.dirname(destination);
  const temporary = path.join(directory, `.${path.basename(destination)}.${process.pid}.${randomUUID()}.tmp`);
  await mkdir(directory, { recursive: true });

  const handle = await open(temporary, "wx");
  try {
    await handle.writeFile(content, "utf8");
    await handle.sync();
  } finally {
    await handle.close();
  }

  try {
    await link(temporary, destination);
    return { created: true };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "EEXIST") {
      return { created: false };
    }
    throw error;
  } finally {
    await unlink(temporary).catch(() => undefined);
  }
}

export async function saveValidationCaseFile(
  validationCase: AnalysisValidationCase,
): Promise<{ filename: string; created: boolean }> {
  const directory = validationDataDirectory();
  const hash = profileHash(validationCase.candidateProfile);
  await writeFileAtomic(
    path.join(profilesDirectory(directory), `${hash}.json`),
    `${JSON.stringify({ candidateProfile: validationCase.candidateProfile }, null, 2)}\n`,
  );

  const record = {
    id: validationCase.id,
    createdAt: validationCase.createdAt,
    jobDescription: validationCase.jobDescription,
    candidateProfileHash: hash,
    result: validationCase.result,
  };
  const filename = `${validationCase.id}.json`;
  const { created } = await writeFileAtomic(
    path.join(directory, filename),
    `${JSON.stringify(record, null, 2)}\n`,
  );
  return { filename, created };
}

/**
 * Reads every persisted validation case from disk, which is the full record
 * of everything ever analyzed on this machine (unlike the browser's
 * localStorage copy, which only covers one browser and can be cleared).
 * Malformed or schema-stale files are skipped rather than failing the whole
 * listing, mirroring loadValidationCases' client-side filtering.
 */
export async function listValidationCaseFiles(): Promise<AnalysisValidationCase[]> {
  const directory = validationDataDirectory();
  let entries: string[];
  try {
    entries = await readdir(directory);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw error;
  }

  const cases: AnalysisValidationCase[] = [];
  for (const entry of entries) {
    if (!entry.endsWith(".json") || entry.startsWith(".")) continue;
    try {
      const raw = JSON.parse(await readFile(path.join(directory, entry), "utf8")) as Record<string, unknown>;
      // New-format files reference the profile text by hash instead of embedding it
      // (see saveValidationCaseFile); legacy files already have candidateProfile inline.
      if (typeof raw.candidateProfile !== "string" && typeof raw.candidateProfileHash === "string") {
        const profileRaw = JSON.parse(
          await readFile(path.join(profilesDirectory(directory), `${raw.candidateProfileHash}.json`), "utf8"),
        ) as Record<string, unknown>;
        raw.candidateProfile = profileRaw.candidateProfile;
      }
      const backfilled = { ...raw, result: backfillLegacyAnalysisResult(raw.result) };
      const parsed = analysisValidationCaseSchema.safeParse(backfilled);
      if (parsed.success) cases.push(parsed.data);
    } catch {
      // Skip unreadable or invalid-JSON files rather than failing the listing.
    }
  }

  return cases.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}
