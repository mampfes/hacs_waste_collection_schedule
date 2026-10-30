import { css } from "lit";
export const styles = css`
  :host {
    display: block;
    min-width: 0;
    height: 100%;
    --wcs-accent: var(--primary-color, #03a9f4);
  }
  ha-card {
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    color: var(--primary-text-color);
    overflow: hidden;
  }
  header {
    padding: 20px 20px 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex: none;
  }
  header ha-icon {
    color: var(--wcs-accent);
  }
  h2 {
    margin: 0;
    font-size: var(--ha-card-header-font-size, 20px);
    line-height: 1.4;
    font-weight: 500;
    overflow-wrap: anywhere;
  }
  .content {
    padding: 0 16px 16px;
    overflow: auto;
    flex: 1;
    min-height: 0;
  }
  .state {
    padding: 16px 4px;
    color: var(--secondary-text-color);
    line-height: 1.6;
    overflow-wrap: anywhere;
  }
  .error {
    color: var(--error-color);
  }
  button {
    font: inherit;
    color: inherit;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
  }
  button:focus-visible {
    outline: 3px solid var(--primary-color);
    outline-offset: -3px;
  }
  .retry {
    background: none;
    border: 1px solid var(--divider-color);
    border-radius: var(--ha-border-radius-sm, 8px);
    min-height: 48px;
    padding: 0 16px;
  }
  .list {
    display: grid;
    gap: 8px;
  }
  .pickup {
    display: flex;
    align-items: center;
    gap: 14px;
    text-align: start;
    min-height: 72px;
    padding: 12px;
    border: 0;
    border-radius: var(--ha-border-radius-lg, 12px);
    background: var(--secondary-background-color);
    width: 100%;
    box-sizing: border-box;
  }
  .pickup:hover {
    background: var(--divider-color);
  }
  .visual {
    width: 48px;
    height: 48px;
    flex: none;
    display: grid;
    place-items: center;
    border-radius: 14px;
    background: var(--card-background-color);
    position: relative;
  }
  .visual:before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    border: 2px solid var(--bin-color, var(--primary-color));
    opacity: 0.65;
    pointer-events: none;
  }
  [hidden] {
    display: none !important;
  }
  .visual ha-icon {
    --mdc-icon-size: 28px;
    color: var(--primary-text-color);
  }
  .visual img {
    height: 42px;
    width: 42px;
    object-fit: contain;
    border-radius: 10px;
  }
  .words {
    min-width: 0;
    flex: 1;
  }
  .name {
    font-weight: 500;
    line-height: 1.45;
    overflow-wrap: anywhere;
  }
  .meta {
    display: block;
    color: var(--secondary-text-color);
    font-size: 0.875rem;
    line-height: 1.5;
    overflow-wrap: anywhere;
    margin-top: 3px;
  }
  .when {
    display: block;
    color: var(--primary-text-color);
    font-weight: 500;
    margin-top: 2px;
  }
  .hero .pickup {
    min-height: 108px;
  }
  .hero .name {
    font-size: 1.15rem;
  }
  .hero .visual {
    width: 64px;
    height: 64px;
  }
  .hero .visual ha-icon {
    --mdc-icon-size: 36px;
  }
  .bins {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(130px, 100%), 1fr));
    gap: 10px;
  }
  .bins .pickup {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    min-height: 170px;
  }
  .bins .words {
    width: 100%;
  }
  .bins .visual {
    width: 56px;
    height: 56px;
  }
  .day {
    font-size: 0.875rem;
    font-weight: 500;
    margin: 16px 4px 8px;
    color: var(--secondary-text-color);
  }
  .day:first-child {
    margin-top: 4px;
  }
  .source {
    display: block;
    font-size: 0.75rem;
    color: var(--secondary-text-color);
    margin-top: 4px;
    overflow-wrap: anywhere;
  }
  @media (prefers-reduced-motion: reduce) {
    * {
      animation: none !important;
      transition: none !important;
    }
  }
  @media (forced-colors: active) {
    .pickup {
      border: 1px solid ButtonText;
    }
    .visual:before {
      border-color: CanvasText;
    }
  }
`;
