# Stadt Frankenberg (Eder)

Support for schedules provided by [Stadt Frankenberg (Eder)](https://www.frankenberg.de/), serving Stadt Frankenberg (Eder), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: frankenberg_de
      args:
        district: DISTRICT (Stadtteil)
        street: STREET (Straße)
```

### Configuration Variables

**district**  
*(String) (required)*

**street**
*(String) (optional): only required if asked for a street on the webpage* 

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: frankenberg_de
      args:
        district: Viermünden
```

```yaml
waste_collection_schedule:
    sources:
    - name: frankenberg_de
      args:
        district: FKB-Kernstadt
        street: Futterhof
```

## How to get the source argument

Find the parameter of your address using [https://abfall.frankenberg.de/online-dienste/](https://abfall.frankenberg.de/online-dienste/) and write them exactly like on the web page.
