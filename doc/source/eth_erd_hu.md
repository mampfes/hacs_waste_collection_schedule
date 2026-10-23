# ÉTH (Érd, Diósd, Ráckeresztúr, Sóskút, Tárnok)

Support for schedules provided by [ÉTH (Érd, Diósd, Ráckeresztúr, Sóskút, Tárnok)](https://www.eth-erd.hu).

Source script for www.eth-erd.hu

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eth_erd_hu
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eth_erd_hu
      args:
        city: "\xC9rd"
        street: "Hord\xF3 utca"
```
