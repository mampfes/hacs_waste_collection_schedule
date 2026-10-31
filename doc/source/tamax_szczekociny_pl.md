# TAMAX (Gmina Szczekociny)

Support for schedules provided by [TAMAX (Gmina Szczekociny)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Szczekociny.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_szczekociny_pl
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
    - name: tamax_szczekociny_pl
      args:
        area: "Szczekociny: 8 Pu\u0142ku U\u0142an\xF3w, Boczna, Centralna, D\u0119bowa\u2026"
```

## How to get the source arguments

Find Gmina Szczekociny (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/. Select your village group or street list exactly as printed on the household PDF. Street choices show the beginning of each list; read its PDF for the complete streets. Use the Trudne wjazdy / domki letniskowe route only if the council has assigned your property to that route. Apartment-block and business schedules are not supported. Mixed recycling includes the plastic/metal, paper and glass bags collected together. Textiles and bulky items go to the collection centre; no undated drop-off or appointment is added.
