# Berliner Stadtreinigungsbetriebe

Support for schedules provided by [Berliner Stadtreinigungsbetriebe](https://bsr.de).

Source for Berliner Stadtreinigungsbetriebe waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        schedule_id: SCHEDULE_ID
```

### Configuration Variables

**schedule_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        schedule_id: 04901100010300413840045A
```

## How to get the source arguments

Visit https://www.bsr.de/abfuhrkalender and enter your street (Straße) and house number (Hausnummer) in the form (you may need to pick your postal code from a list). You'll then see a calendar with your pickup dates. Click the "Downloads" button directly above the calendar, then hover your mouse over either of the two links in the popup (PDF or ICS) and read the link shown at the very bottom of your browser window: part of it is a 24-digit number - that's your schedule_id. On some browsers you can instead right-click a link and copy its address to read the number from there.
