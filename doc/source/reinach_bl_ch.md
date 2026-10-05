# Reinach BL

Support for schedules provided by [Reinach BL](https://www.reinach-bl.ch).

Source for waste collection schedule of Gemeinde Reinach BL, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: reinach_bl_ch
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: reinach_bl_ch
      args:
        zone: Kreis Ost
```

## How to get the source arguments

Select your collection zone (Kreis Ost or Kreis West). You can find your zone on the official Reinach BL waste calendar page at https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender.
