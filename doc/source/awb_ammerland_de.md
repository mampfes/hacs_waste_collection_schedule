# AWB Ammerland

Support for schedules provided by [AWB Ammerland](https://www.awb-ammerland.de) (Abfallwirtschaftsbetrieb Landkreis Ammerland).

Supported municipalities: Apen, Bad Zwischenahn, Edewecht, Rastede, Westerstede, Wiefelstede.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_ammerland_de
      args:
        city: CITY
        street: STREET
        street_section: STREET_SECTION  # optional
        four_weekly_rest: false          # optional
```

### Configuration Variables

**city**
*(string) (required)*

Name of the municipality. One of: `Apen`, `Bad Zwischenahn`, `Edewecht`, `Rastede`, `Westerstede`, `Wiefelstede`.

**street**
*(string) (required)*

Exact street name as shown in the AWB Ammerland app.

**street_section**
*(string) (optional)*

Some streets are divided into sections (e.g. `nördl.d. A 28`). If the street has sections and this argument is omitted, the integration will raise an error and list all valid section names. Leave empty for streets without sections.

**four_weekly_rest**
*(boolean) (optional, default: `false`)*

Set to `true` if a 4-weekly ("vier-wöchentlich") collection interval for the residual waste bin has been officially requested.

## Examples

```yaml
# Edewecht – Schepser Damm (no sections)
waste_collection_schedule:
  sources:
    - name: awb_ammerland_de
      args:
        city: Edewecht
        street: Schepser Damm
```

```yaml
# Westerstede – Ammerlandallee, northern section
waste_collection_schedule:
  sources:
    - name: awb_ammerland_de
      args:
        city: Westerstede
        street: Ammerlandallee
        street_section: "nördl.d. A 28"
```

```yaml
# Wiefelstede – Ahlerskamp with 4-weekly residual waste
waste_collection_schedule:
  sources:
    - name: awb_ammerland_de
      args:
        city: Wiefelstede
        street: Ahlerskamp
        four_weekly_rest: true
```

## How to find your street section

If your street has sections, leave `street_section` out of the configuration and trigger a Home Assistant reload. The error message will list all valid section names for your street.
