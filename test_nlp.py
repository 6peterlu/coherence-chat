from nlp import segment_message

def test_segment_message():
    assert segment_message("taken @ 12:15")[0] == ('taken', '12:15')