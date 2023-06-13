# Recycle Coach / my-waste.mobi

Support for schedules provided by [Recycle Coach](https://recyclecoach.com/),
serving several regions and municipalities in the USA

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: my-waste_mobi
      args:
        street: 123 road way
        city: smithsville
        state: ohio
```

### Configuration Variables

#### Basic Usage

**street**<br>
*(string) (required)* Street address, `123 road way` skip punctuation if
abbreviating road type

**city**<br>
*(string) (required)* Name of your municipality

**state**<br>
*(string) (required)* Name of state, two latter abbreviation of fully spelled
out correctly

#### Alternative / Debugging Usage

If for some reason the above does not get what you want and you want to dig in,
   go ahead over to the [Recycle Coach Homepage][https://recyclecoach.com/) open
   up your browser developer tools on network, and watch as you search for your
   address.

The XHR response you're triggering should have a json blob where you can find
your district_id and project_id.  If you specify these, the script will skip the
lookups and use those directly

**district_id**<br>
*(string) (optional)* district_id provided by
`https://recyclecoach.com/wp-json/rec/v1/cities` endpoint

**project_id**<br>
*(numeric) (optional)* project_id provided by
`https://recyclecoach.com/wp-json/rec/v1/cities` endpoint

**zone_id**<br>
*(string) (optional)*  string built from result set of
`https://api-city.recyclecoach.com/zone-setup/address` endpoint
