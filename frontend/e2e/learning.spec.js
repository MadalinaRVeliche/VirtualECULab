import { test, expect } from "@playwright/test";

test("opens an applied chapter and remembers the theory language", async ({
  page,
}) => {
  await page.goto("/");

  const tabs = page.getByRole("navigation", { name: "Learning sections" });
  await expect(tabs.getByRole("button")).toHaveText([
    "Theory",
    "Quiz",
    "Workbench",
  ]);

  // A contents link should navigate to the chapter's anchor so the section
  // can also be reached directly through its URL fragment.
  const contents = page.getByRole("navigation", { name: "Cuprins" });
  await contents
    .getByRole("link", { name: "Din cadrul CAN la viteza din grafic" })
    .click();
  await expect(page).toHaveURL(/#theory-can-dbc$/);

  await page.getByRole("combobox", { name: "Limba" }).selectOption("en");
  await expect(
    page.getByRole("heading", { name: "Applied theory" }),
  ).toBeVisible();

  // Reload to verify that the language survives a fresh React mount.
  // Check both the saved selection and the translated chapter heading.
  await page.reload();

  await expect(page.getByRole("combobox", { name: "Language" })).toHaveValue(
    "en",
  );
  await expect(
    page.getByRole("heading", {
      name: "From a CAN frame to speed on the graph",
    }),
  ).toBeVisible();
});

test("grades a course quiz, saves it and replaces all ten prompts", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  const quiz = page.getByRole("region", { name: "Course quiz" });

  // Scope the fieldset groups to the answer form so the history
  // section does not count as a question.
  const groups = quiz
    .getByRole("form", { name: "Quiz answers" })
    .getByRole("group");
  await expect(groups).toHaveCount(10);
  const grade = quiz.getByRole("button", { name: "Grade quiz" });
  await expect(grade).toBeDisabled();

  // Choose one answer per question without relying on a particular set
  // or answer key. This test checks the submission flow for any quiz.
  for (const group of await groups.all())
    await group.getByRole("radio").first().check();
  await grade.click();
  const score = quiz.getByText(/^Score: \d+ \/ 10$/);
  await expect(score).toBeVisible();

  const previous = await quiz.locator("legend").allTextContents();
  await quiz.getByRole("button", { name: "New quiz" }).click();
  await expect(score).toHaveCount(0);
  await expect(groups).toHaveCount(10);
  const current = await quiz.locator("legend").allTextContents();

  // Strip display numbering before comparing prompts. Moving an old
  // question to another position must still count as a repeat.
  const prompts = (labels) =>
    labels.map((label) => label.replace(/^\d+\. /, ""));
  expect(new Set(prompts(current)).size).toBe(10);
  expect(
    prompts(current).filter((prompt) => prompts(previous).includes(prompt)),
  ).toEqual([]);

  // Reload the app and open history to check that saved scores are
  // available after the in-memory quiz state has been discarded.
  await page.reload();
  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  await quiz.getByText("Quiz history", { exact: true }).click();
  await expect(quiz.getByText(/^\d+\/10 ·/).first()).toBeVisible();
});
