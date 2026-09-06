import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // validationCaseFileStore.ts reads/writes ../data (outside this app's
  // default trace root), which the file tracer otherwise flags by falling
  // back to tracing the whole project. Widening the root to the repo root
  // makes "data/**" expressible, and excluding it here keeps that PII-bearing
  // folder out of any traced/standalone output.
  outputFileTracingRoot: path.join(__dirname, ".."),
  outputFileTracingExcludes: {
    "**": ["../data/**"],
  },
};

export default nextConfig;
