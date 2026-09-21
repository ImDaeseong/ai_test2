import fs from "node:fs";
import path from "node:path";

const DEFAULT_KEYS_FILE = path.resolve(process.cwd(), "../../../ai_agent/keyinfo/keys.env");

/** Loads only OPENAI_API_KEY from the private shared credential file. */
export function loadSharedOpenAiKey(keysFile = DEFAULT_KEYS_FILE): boolean {
  if (process.env.OPENAI_API_KEY) return true;
  if (!fs.existsSync(keysFile)) return false;

  const line = fs
    .readFileSync(keysFile, "utf8")
    .split(/\r?\n/)
    .map((entry) => entry.trim())
    .find((entry) => entry.startsWith("OPENAI_API_KEY="));
  if (!line) return false;

  const value = line.slice("OPENAI_API_KEY=".length).trim().replace(/^(['"])(.*)\1$/, "$2");
  if (!value) return false;
  process.env.OPENAI_API_KEY = value;
  return true;
}
