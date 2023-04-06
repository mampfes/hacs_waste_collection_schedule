# Awista Starnberg

Awista Starnberg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.awista-starnberg.de/abfallwirtschaftskalender/> and select your municipality.  
- Click on `URL in die Zwischenablage kopieren`.
- Replace the `url` in the example configuration with this link.

## Examples

### Berg, Ahornweg 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://xmlcall.awista-starnberg.de/WasteManagementStarnberg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=162188001&AboID=104609&Fra=P;R;B;S;G
```
