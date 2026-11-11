import { test, expect } from "@playwright/test";

test("shows general and applied theory with three course tabs", async ({ page }) => {
  await page.goto("/");
  const nav = page.getByRole("navigation", { name: "Learning sections" });
  await expect(nav.getByRole("button")).toHaveText(["Theory", "Quiz", "Workbench"]);
  await expect(page.getByRole("heading", { name: /Controller Area Network/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Teorie aplicată" })).toBeVisible();
  await page.getByText("Transmit vehicle speed", { exact: true }).click();
  await expect(page.getByRole("heading", { name: "Signal definition", exact: true })).toBeVisible();
});

test("grades a course quiz, saves it and replaces all ten prompts", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  const quiz = page.getByRole("region", { name: "Course quiz" });
  const groups = quiz.getByRole("form", { name: "Quiz answers" }).getByRole("group");
  await expect(groups).toHaveCount(10);
  const grade = quiz.getByRole("button", { name: "Grade quiz" });
  await expect(grade).toBeDisabled();
  for (const group of await groups.all()) await group.getByRole("radio").first().check();
  await grade.click();
  const score = quiz.getByText(/^Score: \d+ \/ 10$/);
  await expect(score).toBeVisible();
  const previous = await quiz.locator("legend").allTextContents();
  await quiz.getByRole("button", { name: "New quiz" }).click();
  await expect(score).toHaveCount(0);
  await expect(groups).toHaveCount(10);
  const current = await quiz.locator("legend").allTextContents();
  const prompts = (labels) => labels.map((label) => label.replace(/^\d+\. /, ""));
  expect(new Set(prompts(current)).size).toBe(10);
  expect(prompts(current).filter((prompt) => prompts(previous).includes(prompt))).toEqual([]);
  await page.reload();
  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  await quiz.getByText("Quiz history", { exact: true }).click();
  await expect(quiz.getByText(/^\d+\/10 ·/).first()).toBeVisible();
});
