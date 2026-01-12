# Bad Aussee

Support for schedules provided by [Bad Aussee](https://www.badaussee.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: badaussee_at
      args:
        restmuell_zone: ZONE_NUMBER
        biomuell_zone: ZONE_NUMBER
        altpapier_zone: ZONE_NUMBER
```

### Configuration Variables

**restmuell_zone**  
*(string/int) (optional)*

Zone number for residual waste (Restmüll). Typically values are 1-4.

**biomuell_zone**  
*(string/int) (optional)*

Zone number for organic waste (Biomüll). Typically values are 1-4.

**altpapier_zone**  
*(string/int) (optional)*

Zone number for paper waste (Altpapier). Typically values are 1-4.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: badaussee_at
      args:
        restmuell_zone: "4"
        biomuell_zone: "4"
        altpapier_zone: "1"
```

## How to get the source arguments

Visit the [Bad Aussee waste collection calendar](https://www.badaussee.at/system/web/kalender.aspx?sprache=1&menuonr=225254344&typids=225238770,225262538,225262564,225262565) to determine your zone numbers for each waste type. The zones are typically indicated in the calendar entries.

Note: Gelber Sack (yellow bag) is collected for all zones and doesn't require a zone parameter.
