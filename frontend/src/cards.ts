import { LitElement, html, nothing, type PropertyValues } from "lit";
import { styleMap } from "lit/directives/style-map.js";
import { styles } from "./styles";
import {
  addDays,
  countdown,
  displayDate,
  locale,
  normalizeEvents,
  safePicture,
  selectPickups,
  styleFor,
  todayKey,
  timezone,
  validateConfig,
} from "./model";
import { text } from "./localize";
import type {
  CalendarEvent,
  CardConfig,
  EntityState,
  Hass,
  Pickup,
} from "./types";
import "./editor";
type Mode = "next" | "schedule" | "bins";
/** Shared calendar requests across cards, bounded and short lived; no credentials stored. */
const requests = new WeakMap<
  object,
  Map<string, { at: number; promise: Promise<CalendarEvent[]> }>
>();
function load(
  hass: Hass,
  entity: string,
  start: string,
  end: string,
  force: boolean,
) {
  let cache = requests.get(hass.callApi);
  if (!cache) {
    cache = new Map();
    requests.set(hass.callApi, cache);
  }
  const key = JSON.stringify([entity, start, end]);
  const existing = cache.get(key);
  if (!force && existing && Date.now() - existing.at < 30000)
    return existing.promise;
  const promise = hass.callApi<CalendarEvent[]>(
    "GET",
    `calendars/${entity}?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`,
  );
  const record = { at: Date.now(), promise };
  cache.set(key, record);
  if (cache.size > 100) cache.delete(cache.keys().next().value!);
  void promise.catch(() => {
    if (cache.get(key) === record) cache.delete(key);
  });
  return promise;
}
async function discover(hass: Hass): Promise<string[]> {
  const entries = await hass.callWS<
    {
      entity_id: string;
      platform: string;
      disabled_by?: string | null;
      hidden_by?: string | null;
    }[]
  >({ type: "config/entity_registry/list" });
  return entries
    .filter(
      (e) =>
        e.platform === "waste_collection_schedule" &&
        e.entity_id.startsWith("calendar.") &&
        !e.disabled_by &&
        !e.hidden_by,
    )
    .map((e) => e.entity_id);
}
export class WasteCard extends LitElement {
  static override properties = {
    hass: { attribute: false },
    config: { state: true },
    pickups: { state: true },
    loading: { state: true },
    failed: { state: true },
    now: { state: true },
  };
  static override styles = styles;
  declare hass?: Hass;
  declare config: CardConfig;
  declare pickups: Pickup[];
  declare loading: boolean;
  declare failed: string[];
  declare now: Date;
  protected mode: Mode = "next";
  private generation = 0;
  private timer?: ReturnType<typeof setInterval>;
  private unsubscribe?: () => void;
  private lastSignature = "";
  private lastRefresh = 0;
  constructor() {
    super();
    this.config = { type: "custom:waste-collection-next-card" };
    this.pickups = [];
    this.loading = false;
    this.failed = [];
    this.now = new Date();
  }
  static getConfigElement() {
    return document.createElement("waste-collection-card-editor");
  }
  static async getStubConfig(hass: Hass) {
    let entities: string[] = [];
    try {
      entities = await discover(hass);
    } catch {
      /* The visual editor remains available if registry access is restricted. */
    }
    return { entities, days: 30, max_items: 12 };
  }
  setConfig(config: CardConfig) {
    this.config = validateConfig(config);
    this.lastSignature = "";
    this.pickups = [];
    this.failed = [];
    this.generation++;
    if (this.isConnected) void this.refresh();
  }
  getCardSize() {
    return this.mode === "schedule" ? 5 : 4;
  }
  getGridOptions() {
    return {
      columns: 12,
      rows: this.mode === "schedule" ? 5 : "auto",
      min_columns: 6,
      min_rows: this.mode === "next" ? 3 : 4,
    };
  }
  override connectedCallback() {
    super.connectedCallback();
    const event = new CustomEvent("context-request", {
      bubbles: true,
      composed: true,
      cancelable: true,
    }) as CustomEvent & {
      context: string;
      subscribe: boolean;
      callback: (
        states: Record<string, EntityState>,
        unsubscribe?: () => void,
      ) => void;
    };
    event.context = "states";
    event.subscribe = true;
    event.callback = (states, unsubscribe) => {
      this.unsubscribe = unsubscribe;
      this.checkStates(states);
    };
    this.dispatchEvent(event);
    this.timer = setInterval(() => {
      this.now = new Date();
      if (
        Date.now() - this.lastRefresh >= 300000 ||
        this.signature() !== this.lastSignature
      )
        void this.refresh();
    }, 60000);
    void this.refresh();
  }
  override disconnectedCallback() {
    super.disconnectedCallback();
    this.generation++;
    clearInterval(this.timer);
    this.unsubscribe?.();
    this.unsubscribe = undefined;
  }
  protected override updated(changed: PropertyValues) {
    if (changed.has("hass")) {
      if (this.hass) this.checkStates(this.hass.states);
    }
  }
  private signature(states = this.hass?.states) {
    if (!this.hass) return "";
    return JSON.stringify([
      this.config.entities,
      this.config.days,
      todayKey(this.now, timezone(this.hass)),
      timezone(this.hass),
      this.config.entities?.map((e) => [
        states?.[e]?.state,
        states?.[e]?.last_updated,
      ]),
    ]);
  }
  private checkStates(states: Record<string, EntityState>) {
    if (this.signature(states) !== this.lastSignature)
      void this.refresh(states);
  }
  async refresh(states = this.hass?.states, force = false) {
    const hass = this.hass;
    if (!hass || !this.isConnected) return;
    const generation = ++this.generation;
    this.lastSignature = this.signature(states);
    this.lastRefresh = Date.now();
    const entities = this.config.entities ?? [];
    if (!entities.length) {
      this.loading = false;
      this.pickups = [];
      this.failed = [];
      return;
    }
    this.loading = true;
    this.failed = [];
    const days = this.config.days ?? 30;
    const zone = timezone(hass);
    const today = todayKey(new Date(), zone);
    // Widen UTC query by a day on both ends; civil-day filtering below handles every time zone.
    const start = `${addDays(today, -1)}T00:00:00Z`;
    const end = `${addDays(today, days + 1)}T00:00:00Z`;
    const results = await Promise.allSettled(
      entities.map(async (entity) => {
        if (
          !states?.[entity] ||
          ["unavailable", "unknown"].includes(states[entity].state)
        )
          throw new Error(entity);
        return normalizeEvents(
          await load(hass, entity, start, end, force),
          entity,
          zone,
          today,
          days,
        );
      }),
    );
    if (generation !== this.generation || !this.isConnected) return;
    this.pickups = results.flatMap((r) =>
      r.status === "fulfilled" ? r.value : [],
    );
    this.failed = results.flatMap((r, i) =>
      r.status === "rejected" ? [entities[i]!] : [],
    );
    this.now = new Date();
    this.loading = false;
  }
  private moreInfo(entityId: string) {
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        detail: { entityId },
        bubbles: true,
        composed: true,
      }),
    );
  }
  private pickup(p: Pickup, language: string, today: string) {
    const style = styleFor(p, this.config);
    const attrs = this.hass?.states[p.entity]?.attributes;
    const picture =
      this.config.show_pictures !== false
        ? safePicture(style.picture)
        : undefined;
    const color =
      style.color && CSS.supports("color", style.color)
        ? style.color
        : undefined;
    const name = style.name || p.type;
    return html`<button
      class="pickup"
      style=${styleMap({ "--bin-color": color })}
      @click=${() => this.moreInfo(p.entity)}
    >
      ${this.config.show_icons !== false
        ? html`<span class="visual" aria-hidden="true"
            >${picture
              ? html`<img
                    src=${picture}
                    alt=""
                    loading="lazy"
                    @error=${(e: Event) => {
                      const img = e.target as HTMLImageElement;
                      img.hidden = true;
                      img.nextElementSibling?.removeAttribute("hidden");
                    }}
                  /><ha-icon
                    hidden
                    .icon=${style.icon ||
                    attrs?.icon ||
                    "mdi:trash-can-outline"}
                  ></ha-icon>`
              : html`<ha-icon
                  .icon=${style.icon || attrs?.icon || "mdi:trash-can-outline"}
                ></ha-icon>`}</span
          >`
        : nothing}
      <span class="words"
        ><span class="name">${name}</span>
        ${this.config.show_countdown !== false
          ? html`<span class="when"
              >${countdown(p.date, today, language)}</span
            >`
          : nothing}
        ${this.config.show_date !== false
          ? html`<span class="meta"
              ><time datetime=${p.date}
                >${displayDate(p.date, language)}</time
              ></span
            >`
          : nothing}
        ${(this.config.entities?.length ?? 0) > 1
          ? html`<span class="source"
              >${attrs?.friendly_name || p.entity}</span
            >`
          : nothing}
      </span>
    </button>`;
  }
  override render() {
    const language = locale(this.hass, this.config);
    const today = todayKey(this.now, this.hass ? timezone(this.hass) : "UTC");
    const all = selectPickups(this.pickups, this.config);
    let items = all;
    if (this.mode === "next")
      items = all.filter((p) => p.date === all[0]?.date);
    if (this.mode === "bins") {
      const seen = new Set<string>();
      items = all.filter((p) => {
        const key = JSON.stringify([p.entity, p.type]);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    }
    items = items.slice(0, this.config.max_items ?? 12);
    const allFailed =
      this.failed.length === (this.config.entities?.length ?? 0) &&
      this.failed.length > 0;
    let previous = "";
    return html`<ha-card
      ><header>
        <ha-icon icon="mdi:recycle" aria-hidden="true"></ha-icon>
        <h2>${this.config.title ?? text(language, this.mode)}</h2>
      </header>
      <div class="content" aria-busy=${this.loading}>
        ${!this.config.entities?.length
          ? html`<div class="state" role="status">
              ${text(language, "choose")}
            </div>`
          : this.loading
            ? html`<div class="state" role="status">
                ${text(language, "loading")}
              </div>`
            : html`
                ${this.failed.length
                  ? html`<div class="state error" role="status">
                      ${text(language, allFailed ? "error" : "partial")}
                      <div>
                        ${this.failed
                          .map(
                            (e) =>
                              this.hass?.states[e]?.attributes.friendly_name ||
                              e,
                          )
                          .join(", ")}
                      </div>
                      <button
                        class="retry"
                        @click=${() => this.refresh(this.hass?.states, true)}
                      >
                        ${text(language, "retry")}
                      </button>
                    </div>`
                  : nothing}
                ${!items.length && !allFailed
                  ? html`<div class="state" role="status">
                      ${text(language, "empty")}
                    </div>`
                  : nothing}
                <div
                  class=${this.mode === "bins"
                    ? "bins"
                    : this.mode === "next"
                      ? "list hero"
                      : "list"}
                >
                  ${items.map((p) => {
                    const showDay =
                      this.mode === "schedule" && previous !== p.date;
                    previous = p.date;
                    return html`${showDay
                      ? html`<h3 class="day">
                          ${displayDate(p.date, language)}
                        </h3>`
                      : nothing}${this.pickup(p, language, today)}`;
                  })}
                </div>
              `}
      </div></ha-card
    >`;
  }
}
class NextCard extends WasteCard {
  protected override mode: Mode = "next";
}
class ScheduleCard extends WasteCard {
  protected override mode: Mode = "schedule";
}
class BinsCard extends WasteCard {
  protected override mode: Mode = "bins";
}
declare global {
  interface Window {
    customCards?: Array<{
      type: string;
      name: string;
      description: string;
      preview: boolean;
    }>;
  }
}
for (const [tag, ctor, name, description] of [
  [
    "waste-collection-next-card",
    NextCard,
    "Waste Collection · Next pickup",
    "All collections on the next collection day",
  ],
  [
    "waste-collection-schedule-card",
    ScheduleCard,
    "Waste Collection · Schedule",
    "Upcoming collections grouped by day",
  ],
  [
    "waste-collection-bins-card",
    BinsCard,
    "Waste Collection · Bins",
    "The next pickup for each waste type",
  ],
] as const) {
  if (!customElements.get(tag)) customElements.define(tag, ctor);
  window.customCards ??= [];
  if (!window.customCards.some((c) => c.type === tag))
    window.customCards.push({ type: tag, name, description, preview: true });
}
