# AMBnet

AMBnet is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.ambnet.biz> and find the ICS file for your area.
- Use the URL as the `url` parameter.

## Examples

### Ranstadt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.ambnet.biz/Abfall-Ranstadt.ics
```
### Ranstadt-RBB

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.ambnet.biz/Abfall-Ranstadt-RBB.ics
```
### Ranstadt-DO

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.ambnet.biz/Abfall-Ranstadt-DO.ics
```
