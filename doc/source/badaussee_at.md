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

Zone number for residual waste (Restmüll). Valid values are 1-6.

**biomuell_zone**  
*(string/int) (optional)*

Zone number for organic waste (Biomüll). Valid values are 1-4.

**altpapier_zone**  
*(string/int) (optional)*

Zone number for paper waste (Altpapier). Valid values are 1-4.

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

To find your zone numbers:

1. Visit the [Bad Aussee waste collection lookup](https://www.badaussee.at/system/web/zusatzseite.aspx?menuonr=225254344&detailonr=225271040)
2. Enter your street name (Straße) and house number (Hausnummer)
3. The resulting table will show your upcoming collection dates and indicate which zone you are in for each waste type

Note: Gelber Sack (yellow bag) is collected for all zones and doesn't require a zone parameter.
