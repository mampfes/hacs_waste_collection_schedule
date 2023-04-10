# Abfallbehandlungsgesellschaft Havelland mbH (abh)

Abfallbehandlungsgesellschaft Havelland mbH (abh) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.abfall-havelland.de/index.php?page_id=543#> and select your location.  
- Click on `Export der Kalenderdaten` to download the .ics file, then copy the download link of the downloaded file. If your browser does not support to directly copy the download url you can use the developer tools there you can find the path of the file in the onklick section of the a tag for the download button.
- Replace the `url` in the example configuration with this link.

## Examples

### Brieselang, Am Nest

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.abfall-havelland.de/UserFiles/Files/Abfuhrtermine%20Am%20Nest%20Brieselang.ics
```
