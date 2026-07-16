# Comune.Digital

Support for Italian municipalities using the [Comune.Digital](https://comune.digital) app platform (powered by GoodBarber / ww-api.com).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: comune_digital_it
      args:
        city: santostefanodicamastra
```

### Configuration Variables

**city**
*(string) (required)*

The subdomain of your municipality's Comune.Digital website. For example, if the website is `https://santostefanodicamastra.comune.digital`, the value is `santostefanodicamastra`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: comune_digital_it
      args:
        city: santostefanodicamastra
```

## How to find the city identifier

1. Open your municipality's Comune.Digital website in a browser.
2. The city identifier is the subdomain — the part before `.comune.digital` in the URL.
   For example: `https://santostefanodicamastra.comune.digital` → `santostefanodicamastra`.

## Notes

- Schedules are published as "tonight put out" reminders (Italian: *Stasera esporre …*); the source automatically reports the following day as the actual collection date.
- The source works for any Italian municipality that publishes a waste-collection agenda section on their Comune.Digital app. If your municipality's app does not include a waste section, no collections will be returned.
