# Oberndorf bei Schwanenstadt

Support for schedules provided by [Oberndorf bei Schwanenstadt](https://www.oberndorf.ooe.gv.at).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: oberndorf_schwanenstadt_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*
Street name as listed in the Oberndorf bei Schwanenstadt waste calendar.

**hausnummer**
*(string | integer) (required)*
House number as listed in the Oberndorf bei Schwanenstadt waste calendar.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: oberndorf_schwanenstadt_at
      args:
        strasse: "Am Hang"
        hausnummer: "2"
```

## How to get the arguments

Visit [https://www.oberndorf.ooe.gv.at](https://www.oberndorf.ooe.gv.at), pick your street and house number from the waste-calendar dropdowns on the homepage, and use the same values here.
