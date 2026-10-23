# Gmina Środa Śląska

Support for schedules provided by [Gmina Środa Śląska](https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/).

Source for Gmina Środa Śląska, Poland

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_sroda_slaska_pl
      args:
        location: LOCATION
        property_type: PROPERTY_TYPE
```

### Configuration Variables

**location**  
*(string) (required)*

**property_type**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_sroda_slaska_pl
      args:
        location: szczepanow
```

## How to get the source arguments

Visit https://www.com-d.pl/komunalne/harm/sroda-slaska, select your locality or Środa Śląska district, and enter the final part of its URL as `location`. `property_type` is `all` (default), `single_family` or `multi_family`; select the dwelling type when the provider publishes separate schedules.
