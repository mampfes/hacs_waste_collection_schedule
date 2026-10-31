# TAMAX (Gmina Imielno)

Support for schedules provided by [TAMAX (Gmina Imielno)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Imielno.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_imielno_pl
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
    - name: tamax_imielno_pl
      args:
        area: Imielno
```

## How to get the source arguments

Find Gmina Imielno (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/ and select your village. The source reads the printed day-and-Roman-month dates, including holiday exceptions. Mixed waste/bio and recycling use different village groups and are matched independently. The four dated bulky collections also accept complete electrical equipment. Tyres have no separate canonical type. Business calendars are not supported.
