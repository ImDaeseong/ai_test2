import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { JobDescriptionInputPanel } from "./JobDescriptionInputPanel";

function ControlledPanel() {
  const [value, setValue] = useState("");
  return <JobDescriptionInputPanel value={value} onChange={setValue} />;
}

describe("JobDescriptionInputPanel", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("blocks empty input by showing a validation message after the field is touched", async () => {
    const user = userEvent.setup();
    render(<ControlledPanel />);
    const textarea = screen.getByLabelText("채용공고");
    await user.click(textarea);
    await user.tab();
    expect(await screen.findByRole("alert")).toHaveTextContent("채용공고를 입력해 주세요.");
  });

  it("shows a too-short message instead of the empty message once text is typed", async () => {
    const user = userEvent.setup();
    render(<ControlledPanel />);
    const textarea = screen.getByLabelText("채용공고");
    await user.type(textarea, "short text");
    await user.tab();
    expect(await screen.findByRole("alert")).toHaveTextContent("최소 30자 이상 입력해 주세요.");
  });

  it("shows no validation message once enough text is entered", async () => {
    const user = userEvent.setup();
    render(<ControlledPanel />);
    const textarea = screen.getByLabelText("채용공고");
    await user.type(textarea, "a".repeat(40));
    await user.tab();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("imports a JobKorea URL into the job description", async () => {
    const description = "AI 백엔드 개발자 채용 공고입니다. ".repeat(3);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job: { description, sufficient: true } }),
    }));
    const user = userEvent.setup();
    render(<ControlledPanel />);
    await user.type(screen.getByLabelText("채용공고 URL"), "https://www.jobkorea.co.kr/Recruit/GI_Read/1");
    await user.click(screen.getByRole("button", { name: "공고 가져오기" }));
    expect(await screen.findByRole("status")).toHaveTextContent("채용공고를 불러왔습니다.");
    expect(screen.getByLabelText("채용공고")).toHaveValue(description);
  });

  it("does not fill the field with a summary-only import and asks for a paste", async () => {
    const description = "회사 소개와 복리후생만 담긴 요약입니다. ".repeat(3);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job: { description, sufficient: false, title: "백엔드 채용", company: "테스트회사" } }),
    }));
    const user = userEvent.setup();
    render(<ControlledPanel />);
    await user.type(screen.getByLabelText("채용공고 URL"), "https://www.jobkorea.co.kr/Recruit/GI_Read/1");
    await user.click(screen.getByRole("button", { name: "공고 가져오기" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("상세 모집요강을 복사해");
    expect(alert).toHaveTextContent("테스트회사");
    // Partial imports must not populate the analyzable field with summary noise.
    expect(screen.getByLabelText("채용공고")).toHaveValue("");
  });
});
