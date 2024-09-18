# MPGK Katowice

Support for schedules provided by [MPGK Katowice](https://www.mpgk.com.pl/), serving Katowice, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: mpgk_com_pl
      args:
        street: STREET (Ulica)
        number: "NUMBER (Numer)"
        
```

### Configuration Variables

**street**  
*(String) (required)*

**number**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: mpgk_com_pl
      args:
        street: Warszawska
        number: 17
        
```

## How to get the source argument

You can check if your parameters work at <https://www.mpgk.com.pl/dla-mieszkancow/harmonogram-wywozu-odpadow> and write them exactly like aut suggested on the web page.
