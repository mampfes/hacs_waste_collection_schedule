import { LitElement, html } from "lit";
import { locale } from "./model";
import { text, type MessageKey } from "./localize";
import type { CardConfig, Hass } from "./types";
export class WasteCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    config: { state: true },
  };
  declare hass?: Hass;
  declare config: CardConfig;
  setConfig(config: CardConfig) {
    this.config = { ...config };
  }
  override render() {
    if (!this.config || !this.hass) return html``;
    const language = locale(this.hass, this.config);
    const label = (s: { name: string }) =>
      text(language, s.name as MessageKey) ?? s.name;
    const schema = [
      { name: "title", selector: { text: {} } },
      {
        name: "entities",
        required: true,
        selector: {
          entity: {
            multiple: true,
            filter: { domain: "calendar" },
            reorder: true,
          },
        },
      },
      { name: "days", selector: { number: { min: 1, max: 366, mode: "box" } } },
      {
        name: "max_items",
        selector: { number: { min: 1, max: 100, mode: "box" } },
      },
      ...["show_countdown", "show_date", "show_icons", "show_pictures"].map(
        (name) => ({ name, selector: { boolean: {} } }),
      ),
      {
        name: "types",
        selector: {
          object: {
            multiple: true,
            fields: {
              type: {
                label: text(language, "type"),
                required: true,
                selector: { text: {} },
              },
              name: { label: text(language, "name"), selector: { text: {} } },
              icon: { label: text(language, "icon"), selector: { icon: {} } },
              color: { label: text(language, "color"), selector: { text: {} } },
              picture: {
                label: text(language, "picture"),
                selector: { text: {} },
              },
            },
          },
        },
      },
      ...["include_types", "exclude_types"].map((name) => ({
        name,
        selector: {
          select: { multiple: true, custom_value: true, options: [] },
        },
      })),
      { name: "language", selector: { text: {} } },
    ];
    const group = (title: MessageKey, fields: unknown[]) => ({
      type: "expandable",
      name: "",
      flatten: true,
      title: text(language, title),
      schema: fields,
    });
    const formSchema = [
      ...schema.slice(0, 4),
      group("appearance", [...schema.slice(4, 8), schema[11]]),
      group("types", schema.slice(8, 9)),
      group("filters", schema.slice(9, 11)),
    ];
    return html`<ha-form
      .hass=${this.hass}
      .data=${{
        days: 30,
        max_items: 12,
        show_countdown: true,
        show_date: true,
        show_icons: true,
        show_pictures: true,
        ...this.config,
      }}
      .schema=${formSchema}
      .computeLabel=${label}
      @value-changed=${(e: CustomEvent<{ value: CardConfig }>) => {
        e.stopPropagation();
        this.config = { ...e.detail.value, type: this.config.type };
        this.dispatchEvent(
          new CustomEvent("config-changed", {
            detail: { config: this.config },
            bubbles: true,
            composed: true,
          }),
        );
      }}
    ></ha-form>`;
  }
}
if (!customElements.get("waste-collection-card-editor"))
  customElements.define("waste-collection-card-editor", WasteCardEditor);
