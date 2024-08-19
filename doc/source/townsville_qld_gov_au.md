# Townsville

Support for schedules provided by [Townsville](https://townsville.qld.gov.au/), serving Townsville, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: townsville_qld_gov_au
      args:
        property_id: PROPERTY_ID
        
```

### Configuration Variables

**property_id**  
*(String) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: townsville_qld_gov_au
      args:
        property_id: 009fe2d01b9ba090598520202d4bcbc7
        
```

## How to get the source argument

Go to <https://mitownsville.service-now.com/webapps/bin_collection.do> and select your property.  The `property_id` is the last part of the URL after you select your property. For example, if the URL is `https://mitownsville.service-now.com/webapps/bin_collection_calendar.do?property_id=009fe2d01b9ba090598520202d4bcbc7`, then the `property_id` is `009fe2d01b9ba090598520202d4bcbc7`.

If you use the form, that's directly embedded in the <https://townsville.qld.gov.au/> website, you need to open you browser's developer tools and look for the `property_id` in the network tab. The `property_id` is part of the URL of the request to `https://mitownsville.service-now.com/webapps/bin_collection_calendar.do`.
