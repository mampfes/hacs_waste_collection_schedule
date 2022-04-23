# A-Region, Switzerland

Support for schedules provided by [A-Region.ch](https://www.a-region.ch)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: a_region_ch
      args:
        city: CITY
```

### Configuration Variables

**city**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: a_region_ch
      args:
        city: Andwil
```

## How to get the source argument

Open [Abfallkalender A-Region](https://www.a-region.ch/index.php?apid=13875680&apparentid=4618613) which shows a list of all cities. Select your city from the list.
