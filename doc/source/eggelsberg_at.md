# Marktgemeinde Eggelsberg

Support for schedules provided by [Marktgemeinde Eggelsberg](https://www.eggelsberg.at), serving Eggelsberg, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eggelsberg_at
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(String) (required)*

Your collection zone: `A` or `B`. This determines your Bioabfall (organic waste) collection day. All other waste types (Altpapier, Gelber Sack, Restabfall) apply to all zones.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eggelsberg_at
      args:
        zone: "A"
```

## How to get the source argument

Visit [Eggelsberg Müllabfuhrtermine](https://www.eggelsberg.at/Buergerservice/Muellabfuhrtermine) and check which zone (A or B) your address belongs to.
