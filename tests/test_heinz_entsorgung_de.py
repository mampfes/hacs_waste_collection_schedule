import pytest
from waste_collection_schedule.source.heinz_entsorgung_de import Source


def test_heinz_entsorgung_de():
    """Test the heinz_entsorgung_de source."""
    # Test with a known parameter
    param = "yesJWYk53alJXaiMiOMJWYk53alJXagMnRlJXapNmbicCLvJnciQiOBJGblxncoNXYzVWZi4CLzJHdhJ3clNjIioWTv93c0Nici4CLqJWYyhjIiojMyASN9J"
    
    source = Source(param=param)
    entries = source.fetch()
    
    # Check that we got some entries
    assert len(entries) > 0, "Should return at least one waste collection entry"
    
    # Check that each entry has the required attributes
    for entry in entries:
        assert entry.date is not None, "Entry should have a date"
        assert entry.type is not None, "Entry should have a type"
        assert entry.icon is not None, "Entry should have an icon"


if __name__ == "__main__":
    test_heinz_entsorgung_de()
    print("✓ All tests passed!")
