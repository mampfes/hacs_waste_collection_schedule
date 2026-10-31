# Hygea

Support for schedules provided by [hygea.be](https://www.hygea.be/).

**Deprecation notice**: Hygea relaunched its website and no longer serves the calendar this source reads (`displaycal.html` now returns a web page instead of the JSON calendar), so this source returns no collections. The [calendar page](https://www.hygea.be/collectes/collectes-en-porte-porte/calendrier-de-collecte-2026) now embeds the Recycle! calendar. This source is deprecated and will be removed in the next major release. Please switch to the shared [Recycle! source](recycleapp_be.md) (`recycleapp_be`) with your address as on [recycleapp.be](https://www.recycleapp.be):

```yaml
waste_collection_schedule:
  sources:
    - name: recycleapp_be
      args:
        postcode: 7000
        street: Grand-Place
        house_number: 22
```

The old `streetIndex` and `cp` values cannot be converted; enter the postcode, street and house number instead. Waste types are reported with the canonical, localised names of `recycleapp_be`.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hygea_be
      args:
        streetIndex: STREET_INDEX
        cp: POSTAL_CODE
```

The arguments can be found in the URL after visiting the [the calendar](https://www.hygea.be/votre-calendrier-de-collecte.html). Select your city and optionally street to show the schedule for your town. Now check the URL and extract either streetIndex (if available) or postal code from the URL. See also examples below.

### Configuration Variables

**streetIndex**  
*(int)*
Street index, extracted from URL.

**cp**  
*(int)*
Postal code, extracted from URL.

## Example

```yaml
# URL: https://www.hygea.be/votre-calendrier-de-collecte.html?cp=7021&street=&streetIndex=13

waste_collection_schedule:
  sources:
    - name: hygea_be
      args:
        streetIndex: 13
```

```yaml
# URL: https://www.hygea.be/votre-calendrier-de-collecte.html?cp=6560&streetIndex=

waste_collection_schedule:
  sources:
    - name: hygea_be
      args:
        cp: 6560
```
