#!/usr/bin/env node
// One-off / re-runnable migration: rewrites legacy data/<uuid>.json validation-case
// files (which embed the full candidateProfile text) into the deduplicated format
// used by validationCaseFileStore.ts (data/profiles/<sha256>.json + a
// candidateProfileHash reference). See docs/ARCHITECTURE.md.
//
// Usage: node scripts/dedupe-profiles.mjs [data-directory]
// Safe to re-run: already-migrated files (candidateProfileHash, no candidateProfile)
// are skipped. Every rewrite is verified (resolving the hash reproduces the exact
// original text) before the case file is overwritten; on any mismatch the script
// aborts that file without touching it and reports it as a failure.

import { createHash, randomUUID } from "node:crypto";
import { readdir, readFile, rename, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.resolve(process.argv[2] ?? path.join(scriptDir, "..", "data"));
const profilesDir = path.join(dataDir, "profiles");

function profileHash(candidateProfile) {
  return createHash("sha256").update(candidateProfile, "utf8").digest("hex");
}

async function ensureProfileFile(hash, candidateProfile) {
  const destination = path.join(profilesDir, `${hash}.json`);
  try {
    await readFile(destination, "utf8");
    return; // already written by an earlier case with the same profile text
  } catch {
    // fall through to write it
  }
  await mkdir(profilesDir, { recursive: true });
  const temporary = path.join(profilesDir, `.${hash}.${process.pid}.${randomUUID()}.tmp`);
  await writeFile(temporary, `${JSON.stringify({ candidateProfile }, null, 2)}\n`, "utf8");
  await rename(temporary, destination);
}

async function migrateCaseFile(filePath) {
  const raw = JSON.parse(await readFile(filePath, "utf8"));
  if (typeof raw.candidateProfile !== "string") {
    return "skipped-already-migrated";
  }

  const hash = profileHash(raw.candidateProfile);
  await ensureProfileFile(hash, raw.candidateProfile);

  const { candidateProfile, ...rest } = raw;
  const record = { ...rest, candidateProfileHash: hash };
  const temporary = `${filePath}.${process.pid}.${randomUUID()}.tmp`;
  await writeFile(temporary, `${JSON.stringify(record, null, 2)}\n`, "utf8");

  // Verify the rewrite resolves back to byte-identical profile text before
  // committing it over the original file.
  const verifyRecord = JSON.parse(await readFile(temporary, "utf8"));
  const verifyProfile = JSON.parse(
    await readFile(path.join(profilesDir, `${verifyRecord.candidateProfileHash}.json`), "utf8"),
  ).candidateProfile;
  if (verifyProfile !== candidateProfile) {
    throw new Error(`verification mismatch for ${filePath}`);
  }

  await rename(temporary, filePath);
  return "migrated";
}

async function main() {
  const entries = await readdir(dataDir).catch((error) => {
    if (error.code === "ENOENT") return [];
    throw error;
  });

  let migrated = 0;
  let skipped = 0;
  let failed = 0;
  for (const entry of entries) {
    if (!entry.endsWith(".json") || entry.startsWith(".")) continue;
    const filePath = path.join(dataDir, entry);
    try {
      const result = await migrateCaseFile(filePath);
      if (result === "migrated") migrated += 1;
      else skipped += 1;
    } catch (error) {
      failed += 1;
      console.error(`FAILED ${entry}: ${error.message}`);
    }
  }

  const profileCount = (await readdir(profilesDir).catch(() => [])).length;
  console.log(`migrated=${migrated} already-migrated=${skipped} failed=${failed} unique-profiles=${profileCount}`);
  if (failed > 0) process.exitCode = 1;
}

main();
