# ÉTH (Érd, Diósd, Ráckeresztúr, Sóskút, Tárnok)

Support for schedules provided by [ÉTH](https://www.eth-erd.hu/hulladeknaptar), serving Diósd, Érd, Ráckeresztúr, Sóskút, Tárnok, HU.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eth_erd_hu
      args:
        city: CITY_NAME
        street: FULL_STREET_NAME
```

### Configuration Variables

**city**
*(string) (required)*

One of: `Érd`, `Diósd`, `Sóskút`, `Tárnok`, `Ráckeresztúr`

**street**
*(string) (required)*

Full street name including type suffix (e.g. `Hordó utca`, `Amur utca`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eth_erd_hu
      args:
        city: Érd
        street: Hordó utca
```

```yaml
waste_collection_schedule:
  sources:
    - name: eth_erd_hu
      args:
        city: Diósd
        street: Diófasor utca
```
