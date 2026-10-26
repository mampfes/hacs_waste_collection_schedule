export interface EntityState {
  state: string;
  last_updated?: string;
  attributes: {
    friendly_name?: string;
    icon?: string;
    entity_picture?: string;
    [key: string]: unknown;
  };
}
export interface Hass {
  states: Record<string, EntityState>;
  language: string;
  locale?: { language?: string; first_weekday?: string; time_zone?: string };
  config: { time_zone: string };
  callApi<T>(method: string, path: string): Promise<T>;
  callWS<T>(message: Record<string, unknown>): Promise<T>;
}
export interface TypeStyle {
  type: string;
  name?: string;
  icon?: string;
  color?: string;
  picture?: string;
}
export interface CardConfig {
  type: string;
  title?: string;
  entities?: string[];
  days?: number;
  max_items?: number;
  show_countdown?: boolean;
  show_date?: boolean;
  show_icons?: boolean;
  show_pictures?: boolean;
  types?: TypeStyle[];
  include_types?: string[];
  exclude_types?: string[];
  language?: string;
}
export interface CalendarEvent {
  start: { date?: string; dateTime?: string };
  end?: { date?: string; dateTime?: string };
  summary: string;
  description?: string;
}
export interface Pickup {
  date: string;
  type: string;
  entity: string;
}
