# TAMAX (Gmina Janów)

Support for schedules provided by [TAMAX (Gmina Janów)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Janów.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_janow_pl
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
    - name: tamax_janow_pl
      args:
        area: "Jan\xF3w"
```

## How to get the source arguments

Find Gmina Janów (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/. Select your village group exactly as printed on the household PDF. Use Trudne wjazdy only if the council has assigned your property to that route. Apartment-block and business schedules are not supported. Mixed recycling includes the plastic/metal, paper and glass bags collected together. M-PSZOK collections require registration and have no dated appointments in this calendar.
