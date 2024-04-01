# ASPN

Support for schedules provided by [ASPN](https://www.eigenbetrieb-abfallwirtschaft.de/termine/abfuhrtermine.html)

1. Go to [ASPN](https://www.eigenbetrieb-abfallwirtschaft.de/termine/abfuhrtermine.html) and select your city and street.
2. The address of the browser window is changed by the website.
3. Use the ids in the address to configure your waste collection schedule.

**Example:**
- https://www.eigenbetrieb-abfallwirtschaft.de/termine/abfuhrtermine/2024/4/344.html
- for "Rosenweg" in "Forst (Lausitz)"
- **4** is the id of the city
- **344** is the id of the street
- the year will be entered automatically by the script

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aw_lkspn_de
      args:
        city: CITY_ID
        street: STREET_ID
```

### Configuration Variables

**city**  
*(string) (required): The id of your city*

**street**  
*(string) (required): The id of your street*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aw_lkspn_de
      args:
        city: "4"
        street: "344"
```
