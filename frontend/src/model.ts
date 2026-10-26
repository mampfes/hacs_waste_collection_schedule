import type {
  CalendarEvent,
  CardConfig,
  Hass,
  Pickup,
  TypeStyle,
} from "./types";
export function validateConfig(config: CardConfig): CardConfig {
  if (!config || typeof config.type !== "string")
    throw new Error("Card type is required");
  if (
    config.entities !== undefined &&
    (!Array.isArray(config.entities) ||
      config.entities.some(
        (e) => typeof e !== "string" || !/^calendar\.[\w]+$/.test(e),
      ))
  )
    throw new Error("Select calendar entities");
  for (const [key, min, max] of [
    ["days", 1, 366],
    ["max_items", 1, 100],
  ] as const) {
    const n = config[key];
    if (n !== undefined && (!Number.isInteger(n) || n < min || n > max))
      throw new Error(`${key}: ${min}–${max}`);
  }
  for (const key of ["include_types", "exclude_types"] as const) {
    if (
      config[key] !== undefined &&
      (!Array.isArray(config[key]) ||
        config[key]!.some((x) => typeof x !== "string"))
    )
      throw new Error(`${key} must be a list of names`);
  }
  if (
    config.types !== undefined &&
    (!Array.isArray(config.types) ||
      config.types.some(
        (s) =>
          !s ||
          typeof s.type !== "string" ||
          ["name", "icon", "color", "picture"].some(
            (k) =>
              s[k as keyof TypeStyle] !== undefined &&
              typeof s[k as keyof TypeStyle] !== "string",
          ),
      ))
  )
    throw new Error("types must contain waste type styles");
  if (config.language) {
    try {
      new Intl.DateTimeFormat(config.language);
    } catch {
      throw new Error("Invalid language");
    }
  }
  return {
    ...config,
    entities: config.entities ? [...new Set(config.entities)] : undefined,
  };
}
export function locale(hass?: Hass, config?: CardConfig): string {
  return config?.language || hass?.locale?.language || hass?.language || "en";
}
export function timezone(hass: Hass): string {
  return hass.locale?.time_zone === "local"
    ? Intl.DateTimeFormat().resolvedOptions().timeZone
    : hass.config.time_zone;
}
/** Calendar dates are civil days, never parsed as UTC timestamps. */
export function todayKey(now: Date, zone: string): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const p = (key: string) => parts.find((x) => x.type === key)!.value;
  return `${p("year")}-${p("month")}-${p("day")}`;
}
export function dayNumber(key: string): number {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(key)) return NaN;
  const [y, m, d] = key.split("-").map(Number) as [number, number, number];
  const date = new Date(0);
  date.setUTCFullYear(y, m - 1, d);
  date.setUTCHours(0, 0, 0, 0);
  return date.toISOString().slice(0, 10) === key
    ? date.getTime() / 86400000
    : NaN;
}
export function addDays(key: string, days: number): string {
  return new Date((dayNumber(key) + days) * 86400000)
    .toISOString()
    .slice(0, 10);
}
export function normalizeEvents(
  events: CalendarEvent[],
  entity: string,
  zone: string,
  today: string,
  days: number,
): Pickup[] {
  return events.flatMap((event) => {
    let date = event.start?.date;
    if (!date && event.start?.dateTime) {
      const instant = new Date(event.start.dateTime);
      if (Number.isFinite(instant.getTime())) date = todayKey(instant, zone);
    }
    if (
      !date ||
      !Number.isFinite(dayNumber(date)) ||
      typeof event.summary !== "string" ||
      !event.summary.trim()
    )
      return [];
    const delta = dayNumber(date) - dayNumber(today);
    return delta >= 0 && delta < days
      ? [{ date, type: event.summary, entity }]
      : [];
  });
}
export function selectPickups(pickups: Pickup[], config: CardConfig): Pickup[] {
  const seen = new Set<string>();
  return pickups
    .filter((p) => {
      if (
        config.include_types?.length &&
        !config.include_types.includes(p.type)
      )
        return false;
      if (config.exclude_types?.includes(p.type)) return false;
      const key = JSON.stringify([p.date, p.type, p.entity]);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort(
      (a, b) =>
        a.date.localeCompare(b.date) ||
        a.type.localeCompare(b.type) ||
        a.entity.localeCompare(b.entity),
    );
}
export function styleFor(p: Pickup, config: CardConfig): TypeStyle {
  return config.types?.find((s) => s.type === p.type) ?? { type: p.type };
}
export function safePicture(value?: string): string | undefined {
  // Local media and HTTPS images only; avoid script/data URLs and mixed content.
  return value && (/^\/(?!\/)/.test(value) || /^https:\/\//i.test(value))
    ? value
    : undefined;
}
export function displayDate(date: string, language: string): string {
  return new Intl.DateTimeFormat(language, {
    timeZone: "UTC",
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date(`${date}T12:00:00Z`));
}
export function countdown(
  date: string,
  today: string,
  language: string,
): string {
  return new Intl.RelativeTimeFormat(language, { numeric: "auto" }).format(
    dayNumber(date) - dayNumber(today),
    "day",
  );
}
