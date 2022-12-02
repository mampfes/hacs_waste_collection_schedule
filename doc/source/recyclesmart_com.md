# RecycleSmart

Support for schedules povided by [RecycleSmart](https://www.recyclesmart.com/)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: recyclesmart_com
      args:
        email: EMAIL
        password: PASSWORD
```

### Configuration Variables

**email**<br>
*(string) (required)*

**password**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: recyclesmart_com
      args:
        email: abc@example.com
        password: 8WdpR%TZPPdM$n5*$FiRz
```
