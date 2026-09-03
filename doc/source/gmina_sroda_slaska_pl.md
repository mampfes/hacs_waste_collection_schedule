# Gmina Środa Śląska

Waste collection for Gmina Środa Śląska.

The [Gmina Środa Śląska schedule page](https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/) is the official source. It currently directs residents to the COM-D schedule service; the collection provider may change in the future.

Support by [GitHub issues](https://github.com/mampfes/hacs_waste_collection_schedule/issues).

## Configuration via configuration.yaml
```yaml
waste_collection_schedule:
  sources:
    - name: gmina_sroda_slaska_pl
      args:
        location: LOCATION
```

Existing `location_id` configurations cannot be migrated automatically because they identify groups of locations rather than a single COM-D schedule. Replace `location_id` with the location slug for your own locality or district.

### Configuration Variables

**location**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_sroda_slaska_pl
      args:
        location: szczepanow
```

## How to get the source arguments

Open the COM-D schedule linked from the [Gmina Środa Śląska schedule page](https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/), choose your locality or Środa Śląska district, and copy the last part of its URL. For example, use `szczepanow` for `https://www.com-d.pl/komunalne/harm/sroda-slaska/szczepanow`.
