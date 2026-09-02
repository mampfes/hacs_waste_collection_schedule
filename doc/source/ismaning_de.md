# Gemeinde Ismaning – Abfallkalender

Support for the waste collection schedule of the community (Gemeinde) Ismaning, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ismaning_de
      args:
        street: Am Englischen Garten
```

```yaml
waste_collection_schedule:
  sources:
    - name: ismaning_de
      args:
        street: Bahnhofstraße
        street_nr: "5"
```

### Configuration Variables

**street**  
*(string) (required)* Name of the street as listed in the Ismaning waste calendar.

**street_nr**  
*(string) (optional)* House number. Only required for streets that
the Ismaning waste calendar splits into house-number ranges; for other
streets leave it empty. When a value is missing for a street that needs
one, the Home Assistant config flow shows a dropdown of the valid numbers.

## How to get the source arguments

Open the [Abfallkalender](https://ismaning.de/umwelt-energie/abfall/abfallkalender/)
and select your street. If a house-number selection appears, note the
number for your address and provide it as `street_nr`; otherwise leave
`street_nr` empty.
