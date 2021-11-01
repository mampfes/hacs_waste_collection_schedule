# Hygea

Support for schedules provided by [hygea.be](https://www.hygea.be/).

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

**streetIndex**<br>
*(int)*
Street index, extracted from URL.

**cp**<br>
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
