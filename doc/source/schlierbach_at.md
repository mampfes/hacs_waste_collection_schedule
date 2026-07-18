# Marktgemeinde Schlierbach

Support for schedules provided by [Marktgemeinde Schlierbach](https://www.schlierbach.at).

Source for Marktgemeinde Schlierbach waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: schlierbach_at
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: schlierbach_at
      args:
        zone: '1'
```

## How to get the source arguments

The zone argument is optional. Zone '1' adds the 4-weekly Restabfall schedule; zone 'Wohnhausanlagen' adds the Gelbe Tonne schedule for residential complexes. Leave it out to receive all events regardless of zone.
