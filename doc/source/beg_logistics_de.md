# Bremerhavener Entsorgungsgesellschaft mbH

Support for schedules provided by [Bremerhavener Entsorgungsgesellschaft mbH](https://beg-bhv.de).

Source for Bremerhavener Entsorgungsgesellschaft mbH.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: beg_logistics_de
      args:
        street: STREET
        hnr: HNR
        two_weeks: TWO_WEEKS
```

### Configuration Variables

**street**  
*(string) (required)*

**hnr**  
*(string) (required)*

**two_weeks**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: beg_logistics_de
      args:
        street: "Hafenstra\xDFe, Bremerhaven"
        hnr: 2
```
