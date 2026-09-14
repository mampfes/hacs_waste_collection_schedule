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

The URL slug of your locality or Środa Śląska district on the COM-D schedule page, for example `szczepanow`.

**property_type**
*(string) (optional, default: `all`)*

- `single_family`: schedules labelled **Zabudowa jednorodzinna**.
- `multi_family`: schedules labelled **Zabudowa wielorodzinna**.
- `all`: combine all schedules, preserving the previous behavior.

COM-D can publish both dwelling types on the same fraction page (for example,
paper). Set this option to your property type to avoid extra collection dates.
Schedules without a dwelling-type qualification are included for either type.
If a page explicitly offers dwelling-specific schedules but not the requested
type, the source reports an error rather than silently using a different one.

Existing configurations keep the combined schedule until you explicitly select a
property type. In the Home Assistant UI, reconfigure the existing source entry
to set this argument. This option does not filter waste fractions or date ranges;
use the integration's customization settings for waste-type exclusions.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_sroda_slaska_pl
      args:
        location: szczepanow
        property_type: single_family
```

## How to get the source arguments

Open the COM-D schedule linked from the [Gmina Środa Śląska schedule page](https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/), choose your locality or Środa Śląska district, and copy the last part of its URL. For example, use `szczepanow` for `https://www.com-d.pl/komunalne/harm/sroda-slaska/szczepanow`.
