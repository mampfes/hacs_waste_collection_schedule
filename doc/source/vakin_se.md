# Vakin

Support for schedules provided by [Vakin](https://www.vakin.se).

Waste collection schedule for Vakin (Umeå, Nordmaling, and Vindeln), Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vakin_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vakin_se
      args:
        address: "Kajakv\xE4gen 3, T\xE4fte\xE5"
```

## How to get the source arguments

Enter your street name and house number, followed by the town if needed (e.g. `Kajakvägen 3, Täfteå` or `Storgatan 101, Umeå`), as shown in the address search on the [Vakin waste page](https://www.vakin.se/kundserviceochetjanster/sophamtning/narkommersopbilen.4.6252338c1a0c6bd088ed01f.html).
