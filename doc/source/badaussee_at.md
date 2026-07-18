# Bad Aussee

Support for schedules provided by [Bad Aussee](https://www.badaussee.at).

Source for Bad Aussee, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: badaussee_at
      args:
        restmuell_zone: RESTMUELL_ZONE
        biomuell_zone: BIOMUELL_ZONE
        altpapier_zone: ALTPAPIER_ZONE
```

### Configuration Variables

**restmuell_zone**  
*(string) (optional)*

**biomuell_zone**  
*(string) (optional)*

**altpapier_zone**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: badaussee_at
      args:
        restmuell_zone: '1'
        biomuell_zone: '1'
        altpapier_zone: '1'
```

## How to get the source arguments

Find your zone number for residual waste, organic waste and paper on the Bad Aussee waste calendar; leave a field blank to skip that calendar. The Gelber Sack calendar is always included.
