# AWISTA Kommunal GmbH (Düsseldorf)

Support for waste collection schedules provided by [AWISTA Kommunal GmbH](https://www.awista-kommunal.de/abfallkalender), Düsseldorf, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awista_kommunal_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

Alternatively, you can provide a pre-resolved address UUID and skip the address lookup:

```yaml
waste_collection_schedule:
  sources:
    - name: awista_kommunal_de
      args:
        uuid: UUID
```

### Configuration Variables

**street**
*(string) (required if `uuid` is not set)*

Street name, e.g. `Merkurstraße`.

**house_number**
*(string) (required if `uuid` is not set)*

House number, e.g. `45`.

**uuid**
*(string) (optional)*

A pre-resolved address UUID. If set, the address lookup is skipped and `street`/`house_number` are ignored.

## How to find your `uuid`

1. Open [https://www.awista-kommunal.de/abfallkalender](https://www.awista-kommunal.de/abfallkalender).
2. Search for your address.
3. After selecting your address, the browser URL bar shows `https://www.awista-kommunal.de/abfallkalender/<uuid>`.
4. Copy the `<uuid>` part (e.g. `5d1c4832-fd49-4fa7-a4e3-60dbe116cbc0`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awista_kommunal_de
      args:
        street: "Merkurstraße"
        house_number: "45"
```

Example using a UUID:

```yaml
waste_collection_schedule:
  sources:
    - name: awista_kommunal_de
      args:
        uuid: "5d1c4832-fd49-4fa7-a4e3-60dbe116cbc0"
```

## Bin types returned

The service-tier suffix (`(Vollservice)` / `(Teilservice)`) is stripped; only the waste category is returned.

| Provider description         | Returned type    | Icon                  |
| ---------------------------- | ---------------- | --------------------- |
| Restmüll (Vollservice)       | `Restmüll`       | `Icons.GENERAL_WASTE` |
| Bioabfall (Teilservice)      | `Bioabfall`      | `Icons.BIO_KITCHEN`   |
| Papier (Teilservice)         | `Papier`         | `Icons.PAPER`         |
| Wertstofftonne (Vollservice) | `Wertstofftonne` | `Icons.RECYCLING`     |
