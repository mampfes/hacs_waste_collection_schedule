# ÉTH (Érd, Diósd, Nagytarcsa, Sóskút, Tárnok)

Support for schedules provided by [ÉTH](https://www.eth-erd.hu/hulladeknaptar), serving Diósd, Érd, Nagytarcsa, Sóskút, Tárnok, HU.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eth_erd_hu
      args:
        city: CITY_NAME
        street: FULL_STREET_NAME
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**CITY**
*(string) (required)*

**STREET**
*(string) (required)*
without "utca", "út", etc.
not required in Sóskút

**HOUSE_NUMBER**
*(number) (required)*
not required in Sóskút

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eth_erd_hu
      args:
        city: Diósd
        street: Diófasor
        house_number: 10
```