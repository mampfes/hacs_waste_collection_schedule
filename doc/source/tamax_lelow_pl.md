# TAMAX (Gmina Lelów)

Support for schedules provided by [TAMAX (Gmina Lelów)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Lelów.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_lelow_pl
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_lelow_pl
      args:
        area: "Lel\xF3w (bez ul. Spacerowej), Lgota B\u0142otna, Lgota Gawronna"
```

## How to get the source arguments

Find Gmina Lelów (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/. Select the exact household village group; Lelów's Spacerowa street has a separate route. Use Trudne wjazdy only if the council assigned your property to that route. Yellow cells collect mixed waste and bio; red cells collect mixed waste and recycling; brown cells collect ash, classified as Other with the original Popiół label. The dated bulky notice includes furniture and complete electrical equipment. Tyres and construction items have no separate canonical type. Apartment-block and business calendars are not supported.
