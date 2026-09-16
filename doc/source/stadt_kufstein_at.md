# Stadt Kufstein

Support for schedules provided by [Stadt Kufstein](http://www.stadt.kufstein.at).

Waste collection schedule for Stadtgemeinde Kufstein, Tyrol, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_kufstein_at
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
    - name: stadt_kufstein_at
      args:
        strasse: Festung
        hausnummer: '2'
```

## How to get the source arguments

Open http://www.stadt.kufstein.at/system/web/kalender.aspx?menuonr=218502408, pick your street from the 'Strasse wählen' dropdown and then your house number, and use the same values for 'strasse' and 'hausnummer'.
