# MPO Toruń

Support for schedules provided by [MPO Toruń](https://www.mpo.torun.pl).

Source for MPO Toruń (Miejskie Przedsiębiorstwo Oczyszczania), Toruń, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mpo_torun_pl
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mpo_torun_pl
      args:
        street: Warzywna
        house_number: '13'
```

## How to get the source arguments

Open https://harmonogramy-mpo.mga.com.pl/, choose Toruń and use the street and house number exactly as the dropdowns list them (e.g. 'Ludwika Rydygiera', '10/14'); the surname alone ('Rydygiera') also works when it is unique. The site lists mixed and bio waste for every address, and metals and plastics, paper and glass only where they are collected from containers (mostly multi-family buildings). Bagged recyclables of single-family houses are only published in MPO's PDF leaflets and are not included.
