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

test("HA font scale applies to metadata and source names", async ({ page }) => {
  const card = await mount(page, "schedule", {
    entities: ["calendar.waste", "calendar.missing"],
  });
  await page.addStyleTag({ content: "body{--ha-font-size-scale:1.5}" });
  await expect(card.locator(".meta").first()).toHaveCSS("font-size", "21px");
  await expect(card.locator(".source").first()).toHaveCSS("font-size", "18px");
});
test("narrow Sections cards preserve readable labels without overflow", async ({
  page,
}) => {
  const card = await mount(page, "next");
  await card.evaluate((el) => ((el as HTMLElement).style.width = "180px"));
  expect(await card.evaluate((el) => el.scrollWidth <= el.clientWidth)).toBe(
    true,
  );
  expect(
    await card
      .locator(".name")
      .first()
      .evaluate((el) => el.getBoundingClientRect().width),
  ).toBeGreaterThan(80);
});
test("background refresh preserves pickup content and keyboard focus", async ({
  page,
}) => {
  const card = await mount(page, "next");
  await card.locator(".pickup").first().focus();
  await card.evaluate((el) => {
    const c = el as HTMLElement & {
      hass: Hass;
      refresh(states: Hass["states"], force: boolean): Promise<void>;
      finishRefresh: () => void;
    };
    c.hass.callApi = async <T>() =>
      (await new Promise<CalendarEvent[]>(
        (resolve) =>
          (c.finishRefresh = () =>
            resolve([
              { summary: "General waste", start: { date: "2026-10-27" } },
              { summary: "Recycling", start: { date: "2026-10-27" } },
            ])),
      )) as T;
    void c.refresh(c.hass.states, true);
  });
  await expect(card.locator("[aria-busy]")).toHaveAttribute(
    "aria-busy",
    "true",
  );
  await expect(card.locator(".pickup")).toHaveCount(2);
  await expect(card.locator(".pickup").first()).toBeFocused();
  await card.evaluate((el) =>
    (el as HTMLElement & { finishRefresh(): void }).finishRefresh(),
  );
  await expect(card.locator("[aria-busy]")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await expect(card.locator(".pickup").first()).toBeFocused();
});
test("source labels use Home Assistant device/entity naming", async ({
  page,
}) => {
  const card = await mount(page, "schedule", {
    entities: ["calendar.waste", "calendar.missing"],
  });
  await card.evaluate((el) => {
    const c = el as HTMLElement & { hass: Hass };
    c.hass = {
      ...c.hass,
      formatEntityName: () => "Moreton Bay Waste collection",
    };
  });
  await expect(card.locator(".source").first()).toHaveText(
    "Moreton Bay Waste collection",
  );
});

test("retry keeps its error banner and keyboard focus during a refresh", async ({
  page,
}) => {
  const card = await mount(page, "next", {
    entities: ["calendar.waste", "calendar.missing"],
  });
  await card.evaluate((el) => {
    const c = el as HTMLElement & { hass: Hass; finishRetry: () => void };
    c.hass.callApi = async <T>() =>
      (await new Promise<CalendarEvent[]>(
        (resolve) =>
          (c.finishRetry = () =>
            resolve([
              { summary: "General waste", start: { date: "2026-10-27" } },
            ])),
      )) as T;
  });
  const retry = card.getByRole("button", { name: "Retry", exact: true });
  await retry.focus();
  await page.keyboard.press("Enter");
  await expect(card.locator("[aria-busy]")).toHaveAttribute(
    "aria-busy",
    "true",
  );
  await expect(retry).toBeFocused();
  await expect(card).toContainText("Some calendars could not be loaded");
  await card.evaluate((el) =>
    (el as HTMLElement & { finishRetry(): void }).finishRetry(),
  );
  await expect(card.locator("[aria-busy]")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await expect(retry).toBeFocused();
});

test("next pickup shows each calendar's next day under its own heading", async ({
  page,
}) => {
  const card = await mount(page, "next", {
    entities: ["calendar.waste", "calendar.holiday"],
  });
  await card.evaluate(async (el) => {
    const c = el as HTMLElement & {
      hass: Hass;
      refresh(states: Hass["states"], force: boolean): Promise<void>;
    };
    const hass: Hass = {
      ...c.hass,
      states: {
        ...c.hass.states,
        "calendar.holiday": {
          state: "off",
          attributes: { friendly_name: "Holiday house" },
        },
      },
      callApi: async <T>(_: string, path: string) =>
        (path.includes("calendar.holiday")
          ? [{ summary: "Glass", start: { date: "2026-10-29" } }]
          : [
              { summary: "General waste", start: { date: "2026-10-27" } },
              { summary: "Recycling", start: { date: "2026-10-27" } },
            ]) as T,
    };
    c.hass = hass;
    await c.refresh(hass.states, true);
  });
  await expect(card.locator(".day")).toHaveText([
    "Waste collection",
    "Holiday house",
  ]);
  await expect(card.locator(".pickup")).toHaveCount(3);
  await expect(card.locator(".pickup").last()).toContainText("Glass");
  await expect(card.locator(".source")).toHaveCount(0);
});
test("source customize icons apply before the calendar icon", async ({
  page,
}) => {
  const card = await mount(page, "next");
  await card.evaluate((el) => {
    const c = el as HTMLElement & { hass: Hass };
    const state = c.hass.states["calendar.waste"]!;
    c.hass = {
      ...c.hass,
      states: {
        "calendar.waste": {
          ...state,
          attributes: {
            ...state.attributes,
            icon: "mdi:calendar",
            waste_types: { Recycling: { icon: "mdi:recycle" } },
          },
        },
      },
    };
  });
  const icons = card.locator(".visual ha-icon");
  await expect
    .poll(() =>
      icons.evaluateAll((els) =>
        els.map((e) => (e as HTMLElement & { icon: string }).icon),
      ),
    )
    .toEqual(["mdi:calendar", "mdi:recycle"]);
});
test("past days disappear at midnight before the refresh returns", async ({
  page,
}) => {
  const card = await mount(page, "next");
  await card.evaluate((el) => {
    const c = el as HTMLElement & { hass: Hass };
    c.hass.callApi = () => new Promise(() => {});
  });
  // 01:00 on 28 Oct in Brisbane: the 27 Oct pickups are now in the past.
  await page.clock.fastForward("38:00:00");
  await expect(card.locator(".pickup")).toHaveCount(1);
  await expect(card).toContainText("Garden organics");
  await expect(card).not.toContainText("yesterday");
});
test("bins default to a longer window than the other cards", async ({
  page,
}) => {
  await mount(page, "bins");
  const days = await page.evaluate(async () => {
    const hass = { callWS: async () => [] } as unknown as Hass;
    const stub = (tag: string) =>
      (
        customElements.get(tag) as unknown as {
          getStubConfig(h: Hass): Promise<{ days: number }>;
        }
      ).getStubConfig(hass);
    return [
      (await stub("waste-collection-bins-card")).days,
      (await stub("waste-collection-next-card")).days,
    ];
  });
  expect(days).toEqual([90, 30]);
});
test("error banners pass contrast with Home Assistant's default error colour", async ({
  page,
}) => {
  await mount(page, "schedule", {}, undefined, true);
  await page.addScriptTag({ path: "node_modules/axe-core/axe.min.js" });
  const violations = await page.evaluate(async () => {
    const axe = (
      window as unknown as {
        axe: {
          run(
            c: Element,
            o: unknown,
          ): Promise<{ violations: Array<{ id: string }> }>;
        };
      }
    ).axe;
    return (
      await axe.run(document.querySelector("waste-collection-schedule-card")!, {
        rules: { region: { enabled: false } },
      })
    ).violations.map((v) => v.id);
  });
  expect(violations).toEqual([]);
});

test("calendar revisions invalidate cached responses while cards share requests", async ({
  page,
}) => {
  const card = await mount(page, "schedule");
  const counts = await card.evaluate(async (el) => {
    const c = el as HTMLElement & {
      hass: Hass;
      refresh(states: Hass["states"], force?: boolean): Promise<void>;
    };
    let calls = 0;
    let label = "Old pickup";
    c.hass.callApi = async <T>() => {
      calls++;
      return [{ summary: label, start: { date: "2026-10-27" } }] as T;
    };
    await c.refresh(c.hass.states);
    const initial = calls;
    const second = document.createElement(
      "waste-collection-schedule-card",
    ) as HTMLElement & {
      hass: Hass;
      setConfig(c: CardConfig): void;
      refresh(states: Hass["states"]): Promise<void>;
    };
    second.hass = c.hass;
    second.setConfig({
      type: "custom:waste-collection-schedule-card",
      entities: ["calendar.waste"],
    });
    document.getElementById("cards")!.append(second);
    await second.refresh(second.hass.states);
    const shared = calls;
    label = "Updated pickup";
    c.hass.states = {
      "calendar.waste": {
        ...c.hass.states["calendar.waste"]!,
        last_updated: "b",
      },
    };
    await Promise.all([
      c.refresh(c.hass.states),
      second.refresh(c.hass.states),
    ]);
    return [initial, shared, calls];
  });
  expect(counts).toEqual([1, 1, 2]);
  for (const c of await page.locator("waste-collection-schedule-card").all()) {
    await expect(c).toContainText("Updated pickup");
    await expect(c).not.toContainText("Old pickup");
  }
});

test("a failed picture recovers when its source URL changes", async ({
  page,
}) => {
  await page.route("**/local/broken.png", (route) =>
    route.fulfill({ status: 404, body: "missing" }),
  );
  await page.route("**/local/valid.svg", (route) =>
    route.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" fill="green"/></svg>',
    }),
  );
  const card = await mount(page);
  const setPicture = async (picture: string) =>
    card.evaluate((el, picture) => {
      const c = el as HTMLElement & { hass: Hass };
      const state = c.hass.states["calendar.waste"]!;
      c.hass = {
        ...c.hass,
        states: {
          "calendar.waste": {
            ...state,
            attributes: {
              ...state.attributes,
              waste_types: { "General waste": { picture } },
            },
          },
        },
      };
    }, picture);
  await setPicture("/local/broken.png");
  await expect(card.locator("img")).toHaveCount(1);
  await expect(card.locator("img")).toHaveAttribute("hidden", "");
  await expect(
    card.locator(".pickup").first().locator("ha-icon"),
  ).not.toHaveAttribute("hidden", "");
  await setPicture("/local/valid.svg");
  await expect(card.locator("img")).toBeVisible();
  await expect
    .poll(() =>
      card
        .locator("img")
        .evaluate((img) => (img as HTMLImageElement).naturalWidth),
    )
    .toBe(40);
  await expect(card.locator(".pickup").first().locator("ha-icon")).toBeHidden();
});

test("pictures remain enabled when icons are off, including after image failure", async ({
  page,
}) => {
  await page.route("**/local/picture.svg", (route) =>
    route.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"/>',
    }),
  );
  const card = await mount(page, "next", {
    show_icons: false,
    show_pictures: true,
    types: [{ type: "General waste", picture: "/local/picture.svg" }],
  });
  await expect(card.locator("img")).toBeVisible();
  await expect(card.locator(".visual ha-icon")).toHaveCount(0);
  await card.locator("img").dispatchEvent("error", { bubbles: false });
  await expect(card.locator("img")).toBeHidden();
  await expect(card.locator(".visual ha-icon")).toHaveCount(0);
});

test("focus stays on the surviving pickup when refresh inserts and reorders events", async ({
  page,
}) => {
  const card = await mount(page, "schedule");
  const focused = card.getByRole("button", { name: /Garden organics/ });
  await focused.focus();
  await card.evaluate(async (el) => {
    const c = el as HTMLElement & {
      hass: Hass;
      refresh(states: Hass["states"], force: boolean): Promise<void>;
    };
    c.hass.callApi = async <T>() =>
      [
        { summary: "A new collection", start: { date: "2026-10-26" } },
        { summary: "General waste", start: { date: "2026-10-31" } },
        { summary: "Garden organics", start: { date: "2026-10-30" } },
      ] as T;
    await c.refresh(c.hass.states, true);
  });
  await expect(focused).toBeFocused();
  await page.evaluate(() =>
    document.addEventListener("hass-more-info", (e) => {
      document.body.dataset.entity = (e as CustomEvent).detail.entityId;
    }),
  );
  await page.keyboard.press("Enter");
  await expect(page.locator("body")).toHaveAttribute(
    "data-entity",
    "calendar.waste",
  );
});
