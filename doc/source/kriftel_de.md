# Gemeinde Kriftel

Support for schedules provided by [Gemeinde Kriftel](https://www.kriftel.de), serving Kriftel, Hesse, Germany.

Kriftel publishes one ICS calendar file per group of districts and year on its website. This source automatically finds the current download link for the requested district.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kriftel_de
      args:
        district: DISTRICT
```

### Configuration Variables

**district**
*(String) (required)*

The Kriftel collection district your address belongs to: `1`, `2` or `3`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: kriftel_de
      args:
        district: "1"
```

## How to get the source argument

Kriftel is divided into collection districts. Use the number of the district your address belongs to (`1`, `2` or `3`); districts `1` and `3` currently share the same calendar.

You can find the published calendars at [https://www.kriftel.de/rathaus-politik/verwaltung/abfall/](https://www.kriftel.de/rathaus-politik/verwaltung/abfall/).
