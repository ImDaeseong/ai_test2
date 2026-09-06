import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CandidateProfileInputPanel } from "./CandidateProfileInputPanel";

function ControlledPanel() {
  const [value, setValue] = useState("");
  return <CandidateProfileInputPanel value={value} onChange={setValue} />;
}

describe("CandidateProfileInputPanel", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("blocks an empty profile by showing a validation message after the field is touched (docs/PRODUCT.md)", async () => {
    const user = userEvent.setup();
    render(<ControlledPanel />);

    const textarea = screen.getByLabelText("이력서 / 커리어 / 프로젝트");
    await user.click(textarea);
    await user.tab();

    expect(await screen.findByRole("alert")).toHaveTextContent("이력서/커리어 정보를 입력해 주세요.");
  });

  it("shows no validation message once enough text is entered", async () => {
    const user = userEvent.setup();
    render(<ControlledPanel />);

    const textarea = screen.getByLabelText("이력서 / 커리어 / 프로젝트");
    await user.type(textarea, "a".repeat(40));
    await user.tab();

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("loads and persists an attached candidate JSON profile", async () => {
    const user = userEvent.setup();
    render(<ControlledPanel />);
    const file = new File(['{"name":"임대성","projects":["CareerDiff"]}'], "candidate-profile-임대성.json", {
      type: "application/json",
    });
    Object.defineProperty(file, "text", { value: async () => '{"name":"임대성","projects":["CareerDiff"]}' });

    await user.upload(screen.getByLabelText("후보자 프로필 JSON 첨부"), file);

    expect(await screen.findByText("첨부됨: candidate-profile-임대성.json")).toBeInTheDocument();
    expect(screen.getByLabelText("이력서 / 커리어 / 프로젝트")).toHaveValue(
      '{\n  "name": "임대성",\n  "projects": [\n    "CareerDiff"\n  ]\n}',
    );
    expect(window.localStorage.getItem("careerdiff:candidate-profile-filename")).toBe("candidate-profile-임대성.json");
  });

  it("restores the attached profile from local storage", async () => {
    window.localStorage.setItem("careerdiff:candidate-profile", '{"name":"임대성"}');
    window.localStorage.setItem("careerdiff:candidate-profile-filename", "candidate-profile-임대성.json");

    render(<ControlledPanel />);

    expect(await screen.findByText("첨부됨: candidate-profile-임대성.json")).toBeInTheDocument();
    expect(screen.getByLabelText("이력서 / 커리어 / 프로젝트")).toHaveValue('{"name":"임대성"}');
  });
});
