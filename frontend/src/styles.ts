import { css } from "lit";
export const styles = css`
  :host {
    display: block;
    min-width: 0;
    height: 100%;
    font-family: var(--ha-font-family-body, inherit);
    font-size: var(--ha-font-size-m, 14px);
    --wcs-accent: var(--primary-color, #03a9f4);
  }
  .frame {
    container-type: inline-size;
    height: 100%;
    min-width: 0;
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
    padding: var(--ha-space-5, 20px) var(--ha-space-5, 20px)
      var(--ha-space-3, 12px);
    display: flex;
    align-items: center;
    gap: var(--ha-space-3, 12px);
    flex: none;
  }
  header ha-icon {
    color: var(--wcs-accent);
  }
  h2 {
    margin: 0;
    font-family: var(--ha-font-family-heading, inherit);
    font-size: var(--ha-font-size-xl, var(--ha-card-header-font-size, 20px));
    line-height: 1.4;
    font-weight: var(--ha-font-weight-medium, 500);
    overflow-wrap: anywhere;
  }
  .content {
    padding: 0 var(--ha-space-4, 16px) var(--ha-space-4, 16px);
    overflow: auto;
    flex: 1;
    min-height: 0;
  }
  .state {
    padding: 16px 4px;
    color: var(--secondary-text-color);
    line-height: var(--ha-line-height-normal, 1.6);
    overflow-wrap: anywhere;
  }
  /* HA's default error red is below 4.5:1 on light cards: text stays in theme colours. */
  .error {
    display: flex;
    gap: var(--ha-space-3, 12px);
    align-items: flex-start;
    color: var(--primary-text-color);
  }
  .error > ha-icon {
    flex: none;
    color: var(--error-color);
  }
  .failed {
    color: var(--secondary-text-color);
    margin-bottom: 8px;
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
    gap: var(--ha-space-2, 8px);
  }
  .pickup {
    display: flex;
    align-items: center;
    gap: 14px;
    text-align: start;
    min-height: 72px;
    padding: var(--ha-space-3, 12px);
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
    border: 2px solid var(--divider-color);
    pointer-events: none;
  }
  /* Styled types get a tinted tile and a full-strength ring; name and date still carry the meaning. */
  .styled .visual {
    background: color-mix(
      in srgb,
      var(--bin-color) 16%,
      var(--card-background-color)
    );
  }
  .styled .visual:before {
    border-color: var(--bin-color);
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
    font-weight: var(--ha-font-weight-medium, 500);
    line-height: 1.45;
    overflow-wrap: anywhere;
  }
  .meta {
    display: block;
    color: var(--secondary-text-color);
    font-size: var(--ha-font-size-m, 14px);
    line-height: 1.5;
    overflow-wrap: anywhere;
    margin-top: 3px;
  }
  .when {
    display: block;
    color: var(--primary-text-color);
    font-weight: var(--ha-font-weight-medium, 500);
    margin-top: 2px;
  }
  .hero .pickup {
    min-height: 108px;
  }
  .hero .name {
    font-size: var(--ha-font-size-l, 16px);
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
    gap: var(--ha-space-3, 12px);
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
    font-size: var(--ha-font-size-m, 14px);
    font-weight: var(--ha-font-weight-medium, 500);
    margin: 16px 4px 8px;
    color: var(--secondary-text-color);
  }
  .day:first-child {
    margin-top: 4px;
  }
  .source {
    display: block;
    font-size: var(--ha-font-size-s, 12px);
    color: var(--secondary-text-color);
    margin-top: 4px;
    overflow-wrap: anywhere;
  }
  @container (max-width: 240px) {
    header {
      padding: var(--ha-space-3, 12px);
      gap: var(--ha-space-2, 8px);
    }
    h2 {
      font-size: var(--ha-font-size-l, 16px);
    }
    .content {
      padding: 0 var(--ha-space-3, 12px) var(--ha-space-3, 12px);
    }
    .pickup {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--ha-space-2, 8px);
    }
    .hero .visual {
      width: 48px;
      height: 48px;
    }
    .hero .visual ha-icon {
      --mdc-icon-size: 28px;
    }
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
    .visual:before,
    .styled .visual:before {
      border-color: CanvasText;
    }
  }
`;
