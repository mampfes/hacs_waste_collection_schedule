import { test, expect, type Page } from "@playwright/test";
import type { CardConfig, CalendarEvent, Hass } from "../../src/types";
async function mount(
  page: Page,
  mode = "next",
  options: Partial<CardConfig> = {},
  events?: CalendarEvent[],
  failure = false,
) {
  await page.clock.install({ time: new Date("2026-10-26T01:00:00Z") });
  await page.goto("/");
  await page.evaluate(
    async ({ mode, options, events, failure }) => {
      await customElements.whenDefined("waste-collection-next-card");
      const card = document.createElement(
        `waste-collection-${mode}-card`,
      ) as HTMLElement & { hass: Hass; setConfig(c: CardConfig): void };
      const data = events ?? [
        { summary: "General waste", start: { date: "2026-10-27" } },
        { summary: "Recycling", start: { date: "2026-10-27" } },
        { summary: "Garden organics", start: { date: "2026-10-30" } },
        { summary: "Recycling", start: { date: "2026-11-10" } },
      ];
      card.hass = {
        states: {
          "calendar.waste": {
            state: "off",
            last_updated: "a",
            attributes: { friendly_name: "Waste collection" },
          },
        },
        language: "en",
        locale: { language: "en" },
        config: { time_zone: "Australia/Brisbane" },
        callApi: async <T>() => {
          if (failure) throw new Error("Network failed");
          return data as T;
        },
        callWS: async <T>() => [] as T,
      };
      card.setConfig({
        type: `custom:waste-collection-${mode}-card`,
        entities: ["calendar.waste"],
        ...options,
      });
      document.getElementById("cards")!.append(card);
    },
    { mode, options, events, failure },
  );
  const card = page.locator(`waste-collection-${mode}-card`);
  await expect(card.locator("[aria-busy]")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  return card;
}
test("next pickup includes every simultaneous collection and opens more-info with keyboard", async ({
  page,
}) => {
  const card = await mount(page);
  await expect(card.locator(".pickup")).toHaveCount(2);
  await expect(card).toContainText("tomorrow");
  await expect(card).not.toContainText("Garden organics");
  await page.evaluate(() => {
    document.addEventListener(
      "hass-more-info",
      (e) =>
        (document.body.dataset.entity = (e as CustomEvent).detail.entityId),
    );
  });
  await card.locator(".pickup").first().focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("body")).toHaveAttribute(
    "data-entity",
    "calendar.waste",
  );
});
test("schedule groups days and bins show only the next of each type", async ({
  page,
}) => {
  const card = await mount(page, "schedule");
  await expect(card.locator(".pickup")).toHaveCount(4);
  await expect(card.locator(".day")).toHaveCount(3);
  await page.screenshot({
    path: "test-results/waste-schedule-mobile.png",
    fullPage: true,
  });
});
test("bin customisations keep text readable and arbitrary regional labels intact", async ({
  page,
}) => {
  const card = await mount(page, "bins", {
    types: [
      {
        type: "Recycling",
        name: "纸张 / Verre",
        icon: "mdi:glass-fragile",
        color: "#ffeb3b",
      },
    ],
  });
  await expect(card.locator(".pickup")).toHaveCount(3);
  await expect(card).toContainText("纸张 / Verre");
  await expect(card.locator(".name").filter({ hasText: "纸张" })).toHaveCSS(
    "color",
    "rgb(32, 33, 36)",
  );
  await page.screenshot({
    path: "test-results/waste-bins-mobile.png",
    fullPage: true,
  });
});
test("unavailable calendar is an error, never no collections", async ({
  page,
}) => {
  const card = await mount(page, "schedule", {}, undefined, true);
  await expect(card).toContainText("Could not load collections");
  await expect(card).not.toContainText("No collections");
  await expect(card.getByRole("button", { name: "Retry" })).toBeVisible();
});
test("successful empty period is distinct from a failed calendar", async ({
  page,
}) => {
  const card = await mount(page, "schedule", {}, []);
  await expect(card).toContainText("No collections in this period");
});
test("German and unsupported locales preserve date and countdown localization", async ({
  page,
}) => {
  const card = await mount(page, "next", { language: "de-DE" });
  await expect(card).toContainText("Nächste Abholung");
  await expect(card).toContainText("morgen");
});
test("mobile long labels and large text do not overflow", async ({ page }) => {
  const card = await mount(page, "bins", {
    types: [
      {
        type: "Recycling",
        name: "Papierverpackungen und Wertstoffsammlung mit besonders langem Namen",
      },
    ],
  });
  await page.addStyleTag({ content: "html{font-size:24px}" });
  expect(await card.evaluate((e) => e.scrollWidth <= e.clientWidth)).toBe(true);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
test("partial failures retain the good calendar and show a warning", async ({
  page,
}) => {
  const card = await mount(page, "schedule", {
    entities: ["calendar.waste", "calendar.missing"],
  });
  await expect(card).toContainText("Some calendars could not be loaded");
  await expect(card.locator(".pickup")).toHaveCount(4);
});
test("changing configuration during a pending request discards old results", async ({
  page,
}) => {
  const card = await mount(page, "next");
  await card.evaluate(async (el) => {
    const c = el as HTMLElement & {
      hass: Hass;
      setConfig(c: CardConfig): void;
    };
    let finish: (value: CalendarEvent[]) => void = () => {};
    c.hass = {
      ...c.hass,
      callApi: async <T>() =>
        (await new Promise<CalendarEvent[]>(
          (resolve) => (finish = resolve),
        )) as T,
    };
    c.setConfig({
      type: "custom:waste-collection-next-card",
      entities: ["calendar.waste"],
      days: 8,
    });
    c.setConfig({ type: "custom:waste-collection-next-card", entities: [] });
    finish([{ summary: "Stale response", start: { date: "2026-10-27" } }]);
  });
  await expect(card).toContainText("Select your waste collection calendars");
  await expect(card).not.toContainText("Stale response");
});
test("minute tick rolls the local day forward without state changes", async ({
  page,
}) => {
  const card = await mount(page, "next");
  await expect(card).toContainText("tomorrow");
  await page.clock.fastForward("24:00:00");
  await expect(card).toContainText("today");
});
test("three picker entries, sizing, native editor and image failure fallback", async ({
  page,
}) => {
  const card = await mount(page, "next", {
    types: [{ type: "Recycling", picture: "/missing.png" }],
  });
  await expect(card.locator("img")).toBeHidden();
  const data = await page.evaluate(() => {
    const ctor = customElements.get(
      "waste-collection-next-card",
    ) as CustomElementConstructor & { getConfigElement(): HTMLElement };
    return {
      editor: ctor.getConfigElement().tagName,
      cards: (window as unknown as { customCards: unknown[] }).customCards
        .length,
    };
  });
  expect(data).toEqual({ editor: "WASTE-COLLECTION-CARD-EDITOR", cards: 3 });
});
test("light and dark cards pass accessible contrast and semantics checks", async ({
  page,
}) => {
  const card = await mount(page, "bins");
  for (const dark of [false, true]) {
    if (dark)
      await page.addStyleTag({
        content:
          "body{--primary-text-color:#e8eaed;--secondary-text-color:#bdc1c6;--card-background-color:#202124;--secondary-background-color:#303134;--divider-color:#5f6368;--primary-color:#8ab4f8;background:#121212}",
      });
    await page.addScriptTag({ path: "node_modules/axe-core/axe.min.js" });
    const violations = await page.evaluate(async () => {
      const axe = (
        window as unknown as {
          axe: {
            run(
              c: Element,
              o: unknown,
            ): Promise<{ violations: Array<{ id: string; impact: string }> }>;
          };
        }
      ).axe;
      return (
        await axe.run(document.querySelector("waste-collection-bins-card")!, {
          rules: { region: { enabled: false } },
        })
      ).violations;
    });
    expect(violations).toEqual([]);
    await expect(card.locator(".pickup").first()).toHaveCSS(
      "min-height",
      "170px",
    );
  }
});

// The date must remain separate from the label when the countdown is hidden.
test("date-only appearance keeps labels and dates readable", async ({
  page,
}) => {
  const card = await mount(page, "next", { show_countdown: false });
  await expect(card.locator(".when")).toHaveCount(0);
  await expect(
    card.getByRole("button", {
      name: "General waste Tue, Oct 27",
      exact: true,
    }),
  ).toBeVisible();
});
