# Aprica S.p.A.

Support for schedules provided by [Aprica S.p.A.](https://www.apricaspa.it), part of Gruppo A2A. Aprica serves municipalities in the provinces of Brescia, Bergamo, Como, Cremona, Crema, Lodi and others.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: apricaspa_it
      args:
        address: HOUSE_ADDRESS
        house_number: HOUSE_NUMBER
        city: CITY
```

## Configuration variables

**address**
*(string) (required)* : The street name of your address (e.g., `Via Triumplina`).

**house_number**
*(string) (required)* : The house number of your address (e.g., `90`).

**city**
*(string) (required)* : The city of your address (e.g., `Brescia`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: apricaspa_it
      args:
        address: "Via Triumplina"
        house_number: "90"
        city: "Brescia"
```
