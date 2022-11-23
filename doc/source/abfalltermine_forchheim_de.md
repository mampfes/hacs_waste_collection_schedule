# Abfalltermine Forchheim

Support for Landkreis Forchheim schedules provided by [abfalltermine-forchheim.de](https://www.abfalltermine-forchheim.de/) located in Bavaria, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltermine_forchheim_de
      args:
        city: CITY
        area: AREA
```

### Configuration Variables

**city**<br>
*(string) (required)*

**area**<br>
*(string) (required)*

### How to get the source arguments
The arguments can be found on [abfalltermine-forchheim.de](https://www.abfalltermine-forchheim.de/).
Search for your area. Use the part in front of the dash as `city` argument and the part behind it as `area` argument. Do not insert additional spaces.
<br>

**Examples**
Forchheim - Bamberger Straße (nördlich der Adenauerallee)

```yaml
city: Forchheim
area: Bamberger Straße (nördlich der Adenauerallee)
```
<br>
Dormitz - Dormitz

```yaml
city: Dormitz
area: Dormitz
```