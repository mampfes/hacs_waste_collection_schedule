# Depónia Nonprofit Kft.

Support for schedules provided by [Depónia Nonprofit Kft.](https://deponia.hu).

Source for Depónia Nonprofit Kft. waste calendars (Fejér, Veszprém and Komárom-Esztergom counties, plus some settlements in Pest county such as Nagykovácsi, Hungary).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: deponia_hu
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: deponia_hu
      args:
        city: Aba
```

## How to get the source arguments

Open https://deponia.hu/telepuleskereso and pick your settlement. If a street dropdown appears, copy the street name exactly as listed (including house-number ranges such as 'Ady Endre utca 1-20.'). Smaller settlements have a single calendar and do not need a street. No login is needed.
