# AVL - Abfallverwertungsgesellschaft des Landkreises Ludwigsburg mbH

AVL - Abfallverwertungsgesellschaft des Landkreises Ludwigsburg mbH is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.avl-ludwigsburg.de/> and select your location.  
- Click on `URL ANZEIGEN` to get a webcal link.
- Use this link as the `url` parameter.

## Examples

### Sandgrubenweg 27

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://kundenportal.avl-lb.de/WasteManagementLudwigsburg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=941092001&AboID=76574&Fra=BT;RT;PT;LT;GT
```
