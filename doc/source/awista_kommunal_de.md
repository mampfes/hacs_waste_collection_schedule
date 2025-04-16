# Abfalltermine Landkreis Germersheim

Support for City of Düsseldorf, NRW, DE schedules provided by [awista-kommunal.de/abfallkalender](https://www.awista-kommunal.de/abfallkalender)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awista_dus_de
      args:
        Street: Street
```

### Configuration Variables

**street**  
*(string) (required)*

### How to get the source arguments
Provide Street & House No

**Examples**
Prinz-Georg-Straße 40

```yaml
street: Prinz-Georg-Straße 40
```

Erkrather Straße 316

```yaml
city: Erkrather Straße 316
```
