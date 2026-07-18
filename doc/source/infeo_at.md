# infeo

Support for schedules provided by [infeo](https://www.infeo.at/).

Source for INFEO waste collection.

## Configuration via configuration.yaml

### Using zone

```yaml
waste_collection_schedule:
  sources:
    - name: infeo_at
      args:
        customer: CUSTOMER
        zone: ZONE
```

### Using city, street and housenumber

```yaml
waste_collection_schedule:
  sources:
    - name: infeo_at
      args:
        customer: CUSTOMER
        city: CITY
        street: STREET
        housenumber: HOUSENUMBER
```

### Configuration Variables

**customer**  
*(string) (required)*

**zone**  
*(string) (alternative)*

**city**  
*(string) (alternative)*

**street**  
*(string) (alternative)*

**housenumber**  
*(string) (alternative)*

Provide one of: `zone` or `city` + `street` + `housenumber`.

## Example

### Using zone

```yaml
waste_collection_schedule:
  sources:
    - name: infeo_at
      args:
        customer: "bogensch\xFCtz"
        zone: Dettenhausen
```

### Using city, street and housenumber

```yaml
waste_collection_schedule:
  sources:
    - name: infeo_at
      args:
        customer: ikb
        city: Innsbruck
        street: Achselkopfweg
        housenumber: '1'
```
