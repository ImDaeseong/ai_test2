import { NextResponse } from "next/server";
import { OpenAiAnalysisProvider } from "@/core/llm/OpenAiAnalysisProvider";
import type { ProviderStatusResponse } from "@/core/types";

/** Reports the active analysis boundary without exposing credential details. */
export async function GET() {
  const externalProcessing = new OpenAiAnalysisProvider().isConfigured();
  return NextResponse.json<ProviderStatusResponse>({
    mode: externalProcessing ? "openai" : "local",
    externalProcessing,
  });
}
