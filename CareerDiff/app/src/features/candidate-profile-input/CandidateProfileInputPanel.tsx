"use client";

import { useEffect, useRef, useState } from "react";

export const CANDIDATE_PROFILE_MIN_LENGTH = 30;

export function isCandidateProfileValid(value: string): boolean {
  return value.trim().length >= CANDIDATE_PROFILE_MIN_LENGTH;
}

export type CandidateProfileInputPanelProps = {
  value: string;
  onChange: (value: string) => void;
};

const PROFILE_STORAGE_KEY = "careerdiff:candidate-profile";
const PROFILE_FILENAME_STORAGE_KEY = "careerdiff:candidate-profile-filename";

export function CandidateProfileInputPanel({ value, onChange }: CandidateProfileInputPanelProps) {
  const [touched, setTouched] = useState(false);
  const [filename, setFilename] = useState("");
  const [fileError, setFileError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const trimmedLength = value.trim().length;
  const isEmpty = trimmedLength === 0;
  const isTooShort = !isEmpty && trimmedLength < CANDIDATE_PROFILE_MIN_LENGTH;

  useEffect(() => {
    // Deferred to a microtask so state updates happen in a callback rather
    // than synchronously in the effect body (react-hooks/set-state-in-effect).
    queueMicrotask(() => {
      const savedProfile = window.localStorage.getItem(PROFILE_STORAGE_KEY);
      if (savedProfile) onChange(savedProfile);
      setFilename(window.localStorage.getItem(PROFILE_FILENAME_STORAGE_KEY) ?? "");
    });
  }, [onChange]);

  async function attachProfile(file: File | undefined) {
    if (!file) return;
    setFileError("");
    try {
      const parsed = JSON.parse(await file.text()) as unknown;
      const profile = JSON.stringify(parsed, null, 2);
      window.localStorage.setItem(PROFILE_STORAGE_KEY, profile);
      window.localStorage.setItem(PROFILE_FILENAME_STORAGE_KEY, file.name);
      onChange(profile);
      setFilename(file.name);
    } catch {
      setFileError("올바른 JSON 파일을 선택해 주세요.");
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-violet-100 bg-white p-5 shadow-sm shadow-violet-200/40">
      <div className="flex items-center justify-between gap-2">
        <label htmlFor="candidate-profile" className="text-sm font-bold text-violet-900">
          이력서 / 커리어 / 프로젝트
        </label>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="rounded-full border border-violet-200 bg-white px-3 py-1.5 text-sm font-semibold text-violet-700 hover:bg-violet-50"
        >
          {filename ? "재첨부" : "첨부"}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/json,.json"
          aria-label="후보자 프로필 JSON 첨부"
          className="hidden"
          onChange={(event) => {
            void attachProfile(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </div>
      {filename && <p className="text-xs text-green-700">첨부됨: {filename}</p>}
      {fileError && <p role="alert" className="text-xs text-red-600">{fileError}</p>}
      <textarea
        id="candidate-profile"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onBlur={() => setTouched(true)}
        rows={10}
        placeholder="JSON 파일을 첨부하거나 이력서, 커리어 요약, 프로젝트 설명을 붙여넣으세요."
        className="w-full resize-y rounded-xl border border-violet-100 p-3 text-sm focus:border-violet-400 focus:ring-2 focus:ring-violet-200 focus:outline-none"
      />
      <div className="flex min-h-[1rem] items-center justify-between text-xs text-neutral-500">
        <span>{trimmedLength.toLocaleString()}자</span>
        {touched && isEmpty && <span role="alert" className="text-red-600">이력서/커리어 정보를 입력해 주세요.</span>}
        {touched && isTooShort && (
          <span role="alert" className="text-red-600">최소 {CANDIDATE_PROFILE_MIN_LENGTH}자 이상 입력해 주세요.</span>
        )}
      </div>
    </div>
  );
}
