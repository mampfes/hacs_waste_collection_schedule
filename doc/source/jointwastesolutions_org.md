# Joint Waste Solutions

Manages Waste and Recycling services for Woking Borough Council and Surrey Heath Borough Council, in Surrey, UK

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Surrey, please continue to use the source for your current area as long as it's still working. New sources for the new West Surrey council are not expected to be live until at least April 2027, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: jointwastesolutions_org
      args:
        house: HOUSE_NAME_OR_NUMBER
        postcode: POSTCODE
```

### Configuration Variables

**postcode**  
*(string) (required)*

Ensure a space character is included between the two parts of the postcode, For example "GU21 4PQ" rather than "GU214PQ"

**house**  
*(string) (required)*

The name or number of the house. When used in combination with the postcode it should uniquely identify the property. If using the house name, it should match the spelling and format used on the website. House numbers seem to be more reliable than house names.

**borough**  
*(string) (optional) (default: `woking`)*

`woking` or `surreyheath`

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: jointwastesolutions_org
      args:
        house: "4"
        postcode: "GU21 4PQ"
```

```yaml
waste_collection_schedule:
    sources:
    - name: jointwastesolutions_org
      args:
        house: "1"
        postcode: "GU15 1JT"
        borough: "surreyheath",
```
