# PROWOD

Support for schedules provided by [PROWOD](https://prowod.pl).

Source for PROWOD (gmina Dobrzeń Wielki) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: prowod_pl
      args:
        rejon: REJON
```

### Configuration Variables

**rejon**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: prowod_pl
      args:
        rejon: "Dobrze\u0144 Ma\u0142y DW II"
```

## How to get the source arguments

Enter your rejon as named in the calendar links of the yearly announcement on https://prowod.pl/556/harmonogramy-wywozu-odpadow.html: `Dobrzeń Wielki`, `Dobrzeń Mały DW II`, `Chróścice`, `Kup`, `os Energetyk` or `Firmy niezamieszkałe`. Each calendar lists the streets of its rejon at the top.
