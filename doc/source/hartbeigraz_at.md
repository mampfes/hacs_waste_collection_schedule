# Hart bei Graz

Support for schedules provided by [Hart bei Graz](https://www.hartbeigraz.at).

Source for Hart bei Graz, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hartbeigraz_at
      args:
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hartbeigraz_at
      args:
        strasse: "Am Br\xFChlwald"
        hausnummer: '15'
```

## How to get the source arguments

Open https://www.hartbeigraz.at/Service/Muell, pick your street and house number from the dropdowns, and use the same values for 'strasse' and 'hausnummer'.
