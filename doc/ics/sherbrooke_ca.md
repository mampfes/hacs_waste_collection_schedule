# Sherbrooke (QC)

Sherbrooke (QC) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.sherbrooke.ca/fr/services-a-la-population/collecte-des-matieres-residuelles/calendrier-des-collectes>
- Enter your address to retrieve your personalized calendar ICS URL
- Copy the ICS URL (right-click the calendar link and select "Copy link address")
- Use this URL as the `url` parameter.
- Example URL pattern: `https://api.sherbrooke.ca/collection-schedules/calendars/{calendar}/sectors/{sector}/days/{day}/ics`

## Examples

### Sample (Mardi)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.sherbrooke.ca/collection-schedules/calendars/1/sectors/01/days/Mardi/ics
```
