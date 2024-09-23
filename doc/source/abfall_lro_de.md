# Landkreis Rostock

Support for schedules provided by [Landkreis Rostock](https://www.abfall-lro.de/), serving Landkreis Rostock, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: abfall_lro_de
      args:
        municipality: MUNICIPALITY (Gemeinde)
        black_rhythm: BLACK BIN RHYTHM
        green_rhythm: GREEN BIN RHYTHM
        black_seasonal: GREEN BIN SEASONAL (Optional)
        green_seasonal: GREEN BIN SEASONAL (Optional)
```

### Configuration Variables

**municipality**  
*(String) (required)*

**black_rhythm**  
*(String) (required)* Rhythm of the black bin, Should be `2w`, `4w` or empty string ("")

**green_rhythm**  
*(String) (required)* Rhythm of the green bin, Should be `2w`, `4w` or empty string ("")

**black_seasonal**
*(Boolean) (optional)* Weather black bins are only collected Seasonal, Should be `True` or `False`

**green_seasonal**
*(Boolean) (optional)* Weather green bins are only collected Seasonal, Should be `True` or `False`

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: abfall_lro_de
      args:
        municipality: Alt Kätwin
        black_rythm: 2w
        green_rythm: 2w
        black_seasonal: False
        green_seasonal: False
```

## How to get the source argument

Find the parameter of your address using [https://www.abfall-lro.de/de/abfuhrtermine/](https://www.abfall-lro.de/de/abfuhrtermine/) and write them exactly like on the web page.
