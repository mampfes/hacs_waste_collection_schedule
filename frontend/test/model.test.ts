import { describe, it, expect } from "vitest";
import {
  addDays,
  countdown,
  cssColor,
  dayNumber,
  entityName,
  isLiveCalendar,
  nextPickups,
  normalizeEvents,
  safePicture,
  selectPickups,
  todayKey,
  validateConfig,
} from "../src/model";
import type { Hass } from "../src/types";
import { text } from "../src/localize";
const config = { type: "custom:waste-collection-next-card" };
describe("civil dates across regions", () => {
  it("keeps all-day dates independent of time zone", () => {
    for (const zone of [
      "America/Los_Angeles",
      "Europe/Berlin",
      "Australia/Brisbane",
      "Pacific/Kiritimati",
    ]) {
      expect(
        normalizeEvents(
          [{ summary: "纸张", start: { date: "2026-10-26" } }],
          "calendar.waste",
          zone,
          "2026-10-26",
          7,
        )[0]?.date,
      ).toBe("2026-10-26");
    }
  });
  it("uses the installation zone at UTC midnight", () => {
    const now = new Date("2026-10-26T01:00:00Z");
    expect(todayKey(now, "America/Los_Angeles")).toBe("2026-10-25");
    expect(todayKey(now, "Australia/Brisbane")).toBe("2026-10-26");
  });
  it("converts timed events to their local day", () => {
    expect(
      normalizeEvents(
        [{ summary: "Glass", start: { dateTime: "2026-10-26T01:00:00Z" } }],
        "calendar.waste",
        "America/Los_Angeles",
        "2026-10-25",
        3,
      )[0]?.date,
    ).toBe("2026-10-25");
  });
  it("counts calendar days over spring and autumn DST", () => {
    expect(dayNumber("2026-03-30") - dayNumber("2026-03-28")).toBe(2);
    expect(countdown("2026-10-26", "2026-10-25", "en")).toBe("tomorrow");
    expect(addDays("2026-12-31", 1)).toBe("2027-01-01");
  });
  it("rejects invalid dates and past/outside-window events", () => {
    expect(Number.isNaN(dayNumber("2026-02-30"))).toBe(true);
    expect(
      normalizeEvents(
        ["2026-10-25", "2026-10-27", "2026-02-30"].map((date) => ({
          summary: "Glass",
          start: { date },
        })),
        "calendar.waste",
        "UTC",
        "2026-10-26",
        1,
      ),
    ).toEqual([]);
  });
});
describe("provider-neutral selection", () => {
  const picks = [
    { date: "2026-10-27", type: "食品", entity: "calendar.a" },
    { date: "2026-10-26", type: "Verre", entity: "calendar.a" },
    { date: "2026-10-26", type: "Verre", entity: "calendar.b" },
  ];
  it("sorts and deduplicates only within the same calendar", () => {
    expect(selectPickups([...picks, picks[0]!], config)).toEqual([
      picks[1],
      picks[2],
      picks[0],
    ]);
  });
  it("takes the next day of each calendar, in configured order", () => {
    const later = { date: "2026-10-29", type: "Glass", entity: "calendar.b" };
    expect(
      nextPickups([picks[0]!, later, picks[1]!], ["calendar.b", "calendar.a"]),
    ).toEqual([later, picks[1]]);
    expect(nextPickups(picks, ["calendar.a", "calendar.b"])).toEqual([
      picks[1],
      picks[2],
    ]);
  });
  it("filters exact regional labels", () => {
    expect(
      selectPickups(picks, { ...config, include_types: ["食品"] }),
    ).toEqual([picks[0]]);
    expect(
      selectPickups(picks, { ...config, exclude_types: ["Verre"] }),
    ).toEqual([picks[0]]);
  });
  it("validates bounded options and calendar IDs", () => {
    expect(() => validateConfig({ ...config, days: 0 })).toThrow();
    expect(() =>
      validateConfig({ ...config, entities: ["sensor.waste"] }),
    ).toThrow();
    expect(() =>
      validateConfig({
        ...config,
        types: [{ type: "Glass", color: 42 } as never],
      }),
    ).toThrow();
    expect(
      validateConfig({
        ...config,
        entities: ["calendar.waste", "calendar.waste"],
      }).entities,
    ).toEqual(["calendar.waste"]);
  });
  it("accepts safe user images and rejects executable/mixed-content URLs", () => {
    expect(safePicture("/local/bin.svg")).toBe("/local/bin.svg");
    expect(safePicture("https://example.org/bin.png")).toBeTruthy();
    for (const url of [
      "javascript:alert(1)",
      "data:image/svg+xml,test",
      "//remote.example/bin.png",
      "http://example.org/bin.png",
    ])
      expect(safePicture(url)).toBeUndefined();
  });
  it("localizes supported UI languages and falls back for other regions", () => {
    expect(text("de-DE", "next")).toBe("Nächste Abholung");
    expect(text("ja-JP", "next")).toBe("Next collection");
    expect(countdown("2026-10-26", "2026-10-26", "ja-JP")).toBe("今日");
  });
});

describe("HA entity naming", () => {
  it("uses the native formatter on2026.11 and friendly names on older frontends", () => {
    const hass = {
      states: {
        "calendar.waste": {
          state: "off",
          attributes: { friendly_name: "Old friendly name" },
        },
      },
    } as unknown as Hass;
    expect(entityName(hass, "calendar.waste")).toBe("Old friendly name");
    hass.formatEntityName = () => "Moreton Bay Waste collection";
    expect(entityName(hass, "calendar.waste")).toBe(
      "Moreton Bay Waste collection",
    );
    expect(entityName(hass, "calendar.missing")).toBe("calendar.missing");
  });
});

describe("live calendar discovery filter", () => {
  const hass = (states: Hass["states"]) => ({ states }) as Hass;
  it("accepts calendars with a live non-unavailable state", () => {
    expect(
      isLiveCalendar(
        hass({
          "calendar.live": { state: "2026-11-10", attributes: {} },
        }),
        "calendar.live",
      ),
    ).toBe(true);
  });
  it("rejects missing, unavailable, unknown and restored entities", () => {
    const h = hass({
      "calendar.gone": { state: "unavailable", attributes: {} },
      "calendar.unk": { state: "unknown", attributes: {} },
      "calendar.rest": { state: "idle", attributes: { restored: true } },
    });
    expect(isLiveCalendar(h, "calendar.missing")).toBe(false);
    expect(isLiveCalendar(h, "calendar.gone")).toBe(false);
    expect(isLiveCalendar(h, "calendar.unk")).toBe(false);
    expect(isLiveCalendar(h, "calendar.rest")).toBe(false);
    expect(isLiveCalendar(undefined, "calendar.live")).toBe(false);
  });
});
describe("cssColor", () => {
  it("keeps supported colors and drops invalid ones", () => {
    const previous = globalThis.CSS;
    Object.defineProperty(globalThis, "CSS", {
      configurable: true,
      value: {
        supports: (_prop: string, value: string) => value.startsWith("#"),
      },
    });
    try {
      expect(cssColor("#ffeb3b")).toBe("#ffeb3b");
      expect(cssColor("not-a-color")).toBeUndefined();
      expect(cssColor(undefined)).toBeUndefined();
    } finally {
      Object.defineProperty(globalThis, "CSS", {
        configurable: true,
        value: previous,
      });
    }
  });
});
