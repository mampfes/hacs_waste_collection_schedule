# Testing South Cambridgeshire Integration

This guide explains how to test the South Cambridgeshire waste collection integration.

## Method 1: Using the Built-in Test Script (Recommended)

The repository includes a test script that can test individual sources:

```bash
# Navigate to the test directory
cd custom_components/waste_collection_schedule/waste_collection_schedule/test

# Run the test for South Cambridgeshire
python3 test_sources.py -s scambs_gov_uk -l
```

This will:
- Test both test cases defined in the source file
- Show the retrieved collection entries with dates and bin types
- Display any errors that occur

### Expected Output

If successful, you should see output like:
```
Testing source scambs_gov_uk ...
  houseNumber: success
    2025-12-16: Black Bin
    2025-12-23: Blue Bin
    2025-12-30: Green Bin
    ...
  houseName: success
    2025-12-16: Black Bin
    ...
```

## Method 2: Manual Testing with Python

You can test the integration directly with Python:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, 'custom_components/waste_collection_schedule')

from waste_collection_schedule.source.scambs_gov_uk import Source

# Test with a postcode and house number
source = Source(post_code="CB236GZ", number="53")
entries = source.fetch()

# Display results
for entry in sorted(entries, key=lambda x: x.date):
    print(f"{entry.date}: {entry.type} ({entry.icon})")
```

Save this as `test_scambs.py` and run:
```bash
python3 test_scambs.py
```

## Method 3: Testing in Home Assistant

To test in a live Home Assistant installation:

1. **Install the integration** in Home Assistant (if not already installed)

2. **Add to configuration.yaml**:
```yaml
waste_collection_schedule:
  sources:
    - name: scambs_gov_uk
      args:
        post_code: "CB236GZ"
        number: "53"
```

3. **Restart Home Assistant**

4. **Check the logs** for any errors:
   - Go to Settings → System → Logs
   - Filter for "scambs" or "waste_collection"

5. **Verify entities are created**:
   - Go to Developer Tools → States
   - Look for entities starting with `sensor.scambs_gov_uk_`

6. **View the schedule**:
   - The entities should show upcoming bin collection dates
   - Check entity attributes for detailed information

## Test Cases Included

The integration includes two test cases:

1. **houseNumber**: Tests with numeric house number
   - Postcode: CB236GZ
   - Number: 53

2. **houseName**: Tests with house name
   - Postcode: CB225HT
   - Number: "Rectory Farm Cottage"

## Troubleshooting

### Connection Errors
If you see connection errors, this could be due to:
- Network restrictions
- The API being temporarily unavailable
- Rate limiting by the API

The integration now includes:
- 30-second timeouts to prevent hanging
- Graceful degradation if the initial session setup fails
- Detailed logging of errors

### Finding Your Postcode and House Number

1. Go to: https://www.scambs.gov.uk/recycling-and-bins/find-your-household-bin-collection-day/
2. Enter your postcode
3. Select your address from the dropdown
4. Use the house number or name shown in the dropdown for the `number` parameter

### Debug Logging

To enable debug logging in Home Assistant, add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.waste_collection_schedule: debug
```

This will show detailed information about the API requests and responses.

## What Changed in This Update

The improvements make the integration more robust:

1. **Session Management**: Visits the main website before API calls
2. **User-Agent Header**: Mimics a real browser to prevent blocking
3. **Timeouts**: Prevents hanging on network issues (30 seconds per request)
4. **Better Error Handling**: Uses specific HTTP exceptions with clear logging

These changes follow the pattern from the proven working [UKBinCollectionData](https://github.com/robbrad/UKBinCollectionData) implementation.

## Verifying the Improvements

To verify the session management is working, you can check the logs:
- If session setup succeeds: No warnings
- If session setup fails: Warning logged, but integration continues
- API calls should still succeed even if session setup fails

## Need Help?

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify your postcode and house number are correct on the council website
3. Try the test script first to isolate configuration issues
4. Check that the API endpoint is accessible from your network
