# Recycle Coach / recyclecoach.com

Support for schedules provided by [Recycle Coach](https://recyclecoach.com/),
serving several regions and municipalities in North America.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: recyclecoach_com 
      args:
        street: 250 Main St
        city: Port Dover
        state: Ontario
```

### Configuration Variables

#### Basic Usage

**street**<br>
*(string) (required)* Street address, `250 Main St` skip punctuation if
abbreviating road type

**city**<br>
*(string) (required)* Name of your municipality

**state**<br>
*(string) (required)* Name of state or providence (or two latter abbreviation)

#### Alternative / Debugging Usage

If the above does not get what you want or you don't want to use your address in
requests, you can alternatively use your `district_id`, `project_id`, and
`zone_id` to get your collection schedules.

To find out your `district_id` and `project_id`, navigate to the following URL
in your browser: 

    https://api-city.recyclecoach.com/city/search?term=<city>, <state/providence>, <country>
    
Replace the placeholders. (For the United States, the country will be `USA`.)
The spaces after the commas are **required**. As an example, we'll use the
address: 250 Main St, Port Dover, Ontario, Canada.

    https://api-city.recyclecoach.com/city/search?term=Port Dover, Ontario, CA
    
The result will be some JSON, which will contain keys for `disctrict_id` and
`project_id`. In this exacmple,

    ... ,"project_id":"3107","district_id":"OLYMP", ...

If you can't get you location to work in that URL, you can also go to the
[Recycle Coach Homepage](https://recyclecoach.com/) and open the dev tools in your browser. (In Firefox,
three horizontal line button, More tools, Web Developer Tools. Then go to the
Console tab.) Now, search for your city in the box on the homepage. In the
Console, there should be a line with the JSON response (it'll probably be at
the bottom). That JSON should have the `project_id` and `district_id`
mentioned above.

Now, to get the `zone_id`, use the following URL:

    https://api-city.recyclecoach.com/zone-setup/address?sku=<project_id>&district=<district_id>&prompt=undefined&term=<specific address>

Use the `project_id` and `district_id` from the last step. Replace
`<specific address>` with your specific address.

For example:

    https://api-city.recyclecoach.com/zone-setup/address?sku=3107&district=OLYMP&prompt=undefined&term=250 Main St

This will produce another JSON blob, which contains some potential matches.
Each result will have a "zones" key. Pick the best match, probably the first on the list.

    ... ,"zones":{"2447":"z11266","4085":"z16205","4086":"z16208","4087":"z16218"}, ...
    
The numbers prefixed with a "z" are the values we want. Just string them
together. From the result above, the `zone_id` will be `zone-z11266-z16205-z16208-z16218`.

**district_id**<br>
*(string) (optional)* district_id provided by
`https://recyclecoach.com/wp-json/rec/v1/cities` endpoint

**project_id**<br>
*(numeric) (optional)* project_id provided by
`https://recyclecoach.com/wp-json/rec/v1/cities` endpoint

**zone_id**<br>
*(string) (optional)*  string built from result set of
`https://api-city.recyclecoach.com/zone-setup/address` endpoint

And finally, we can use the `district_id`, `project_id`, and `zone_id` in the
config.
```yaml
waste_collection_schedule:
    sources:
    - name: recyclecoach_com 
      args:
        district_id: "OLYMP"
        project_id: 3107
        zone_id: "zone-z11266-z16205-z16208-z16218"
```
