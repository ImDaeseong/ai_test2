import { link, mkdir, open, readdir, readFile, unlink } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
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

export async function saveValidationCaseFile(
  validationCase: AnalysisValidationCase,
): Promise<{ filename: string; created: boolean }> {
  const directory = validationDataDirectory();
  const filename = `${validationCase.id}.json`;
  const destination = path.join(directory, filename);
  const temporary = path.join(directory, `.${validationCase.id}.${process.pid}.${randomUUID()}.tmp`);
  await mkdir(directory, { recursive: true });

  const handle = await open(temporary, "wx");
  try {
    await handle.writeFile(`${JSON.stringify(validationCase, null, 2)}\n`, "utf8");
    await handle.sync();
  } finally {
    await handle.close();
  }

  try {
    await link(temporary, destination);
    return { filename, created: true };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "EEXIST") {
      return { filename, created: false };
    }
    throw error;
  } finally {
    await unlink(temporary).catch(() => undefined);
  }
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
      const backfilled = { ...raw, result: backfillLegacyAnalysisResult(raw.result) };
      const parsed = analysisValidationCaseSchema.safeParse(backfilled);
      if (parsed.success) cases.push(parsed.data);
    } catch {
      // Skip unreadable or invalid-JSON files rather than failing the listing.
    }
  }

  return cases.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}
