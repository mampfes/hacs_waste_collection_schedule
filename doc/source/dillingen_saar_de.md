# Stadt Dillingen Saar Abfuhr

Support for schedules provided by <https://www.dillingen-saar.de/rathaus/buergerservice/abfuhrkalender/>.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dillingen_saar_de
      args:
        street: <Straße>
```

### Configuration Variables

**street**  
_(string) (required)_


## Example


**Configuration via configuration.yaml**

```yaml
waste_collection_schedule:
  sources:
    - name: dillingen_saar_de
      args:
        street: "Odilienplatz"
```


## How to get the source arguments

1. Open <https://www.dillingen-saar.de/rathaus/buergerservice/abfuhrkalender/>.
2. Fill out the search field "Straßenname" to verify your street can be found (field is found below the colored icons).
3. Click on the proposed street name in the call out box displayed after entering of (2).
4. Copy the _complete_ name of the street of this field and paste it to the field `street` in your config.yaml of wastecalendar
