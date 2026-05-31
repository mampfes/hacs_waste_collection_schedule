# Waste Management (WM)

Support for [Waste Management](https://www.wm.com) residential pickup schedules across the United States and Canada.

Uses the same guest address lookup as the [WM Pickup ETA page](https://www.wm.com/us/en/mywm/my-services/view-pickup-eta) — **no MyWM account required**.

## Configuration

### Configuration Variables

**street** *(string) (required)*
Street address, e.g. `1081 Nash Ave`

**city** *(string) (required)*
City name, e.g. `Ypsilanti`

**state** *(string) (required)*
Two-letter state code, e.g. `MI`

**zip_code** *(string) (required)*
5-digit ZIP code, e.g. `48198`

**country** *(string) (optional, default: `US`)*
Country code — `US` or `CA`

---

### Configuration via `configuration.yaml`

```yaml
waste_collection_schedule:
  sources:
    - name: wm_com
      args:
        street: "1081 Nash Ave"
        city: "Ypsilanti"
        state: "MI"
        zip_code: "48198"
```

### Configuration via the Home Assistant UI

Go to **Settings → Devices & Services → Add Integration**, search for **Waste Collection Schedule**, select **United States** as the country, and choose **Waste Management (WM)** from the provider list. Enter your service address when prompted.

---

## Notes

- **No account needed.** This source uses WM's public guest lookup — the same one available at wm.com without logging in.
- **Municipal/franchise customers supported.** Addresses where the township contracts with WM (rather than individual residential accounts) work correctly with this approach.
- **All service types returned.** Trash, recycling, yard waste, and any other active services on the account are returned automatically.
- **Holiday adjustments.** When WM shifts a pickup due to a holiday, the adjusted date is reflected.
- **API key rotation.** WM's internal API keys are embedded in their web application and may be rotated periodically. If the source stops working, please open an issue at the [HACS Waste Collection Schedule repository](https://github.com/mampfes/hacs_waste_collection_schedule/issues).

---

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wm_com
      args:
        street: "1081 Nash Ave"
        city: "Ypsilanti"
        state: "MI"
        zip_code: "48198"
```
