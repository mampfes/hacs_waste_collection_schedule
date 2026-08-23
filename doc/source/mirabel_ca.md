# Mirabel

Waste collection schedules provided by [Collectes et écocentres](https://mirabel.ca/collectes).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mirabel_ca
      args:
        zone: ZONE
```

### Configuration Variables
* **zone** *(string or int) (required)*

**Accepted values:**
- `1`
- `2`
- `3`
- `4`
- `5`
- `6`
- `7`
- `8`

**How do I find my zone number?**

* Visit https://mirabel.ca/services/services-en-ligne/trouver-ma-zone-de-collecte
* Use the search function to display your zone number

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mirabel_ca
      args:
        zone: 1
```
