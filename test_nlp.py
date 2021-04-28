from freezegun import freeze_time
from datetime import datetime
from pytz import utc
from nlp import segment_message

@freeze_time("2000-01-01 18:00:00")
def test_segment_message():
    assert segment_message("T")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}
    assert segment_message("T!")[0] == {'type': 'take', 'modifiers': {'emotion': 'excited'}, "raw": "T!"}
    # assert segment_message("taken @ 12:15")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 12, 15, tzinfo=utc), "raw": "taken @ 12:15"}
    assert segment_message("1")[0] == {'type': 'special', 'payload': '1', "raw": "1"}
    assert segment_message("x")[0] == {'type': 'special', 'payload': 'x', "raw": "x"}
    assert segment_message("1hr")[0] == {'type': 'requested_alarm_time', 'payload': datetime(2000, 1, 1, 19, 0, tzinfo=utc), "raw": "1hr"}
    assert segment_message("1 hour")[0] == {'type': 'requested_alarm_time', 'payload': datetime(2000, 1, 1, 19, 0, tzinfo=utc), "raw": "1 hour"}
    assert segment_message("2hr")[0] == {'type': 'requested_alarm_time', 'payload': datetime(2000, 1, 1, 20, 0, tzinfo=utc), "raw": "2hr"}
    assert segment_message("10 min")[0] == {'type': 'requested_alarm_time', 'payload': datetime(2000, 1, 1, 18, 10, tzinfo=utc), "raw": "10 min"}
    assert segment_message("20")[0] == {'type': 'delay_minutes', 'payload': 20, "raw": "20"}
    # assert segment_message("T at 8:00")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 8, 0, tzinfo=utc), "raw": "T at 8:00"}
    # assert segment_message("T at 8")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 8, 0, tzinfo=utc), "raw": "T at 8"}
    # assert segment_message("T at8")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 8, 0, tzinfo=utc), "raw": "T at8"}
    # assert segment_message("T@8")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 8, 0, tzinfo=utc), "raw": "T@8"}
    # assert segment_message("Taken@ 8")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 8, 0, tzinfo=utc), "raw": "Taken@ 8"}
    # assert segment_message("T at 12:30")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 12, 30, tzinfo=utc), "raw": "T at 12:30"}
    # assert segment_message("T at 1:30pm")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 13, 30, tzinfo=utc), "raw": "T at 1:30pm"}
    assert segment_message("2 on a walk")[0] == {'payload': '2', 'type': 'special', "raw": "2 on a walk"}
    assert segment_message("2 on a walk")[1] == {"payload": {"response": "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.", 'type': 'short', 'concept': 'leisure'}, "type": "activity", "raw": "2 on a walk"}
    # assert segment_message("T @ 0759")[0] == {'modifiers': {'emotion': 'neutral'}, 'payload': datetime(2000, 1, 1, 7, 59, tzinfo=utc), "type": "take", "raw": "T @ 0759"}
    assert segment_message("T. Thanks!")[0] == {'modifiers': {'emotion': 'excited'}, 'type': 'take', "raw": "T. Thanks!"}
    assert segment_message("T. Thanks!")[1] == {'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}
    assert segment_message("Thank you! 5 minutes")[0] == {'type': 'requested_alarm_time', 'payload': datetime(2000, 1, 1, 18, 5, tzinfo=utc), "raw": "Thank you! 5 minutes"}
    assert segment_message("Thank you! 5 minutes")[1] == {'type': 'thanks', 'modifiers': {'emotion': 'excited'}, "raw": "Thank you! 5 minutes"}
    assert segment_message("S :)")[0] == {'type': 'skip', "raw": "S :)"}
    assert segment_message("walking")[0] == {'type': 'activity', 'payload': {'type': 'short', 'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.", 'concept': 'leisure'}, 'raw': 'walking'}
    assert segment_message("dinner")[0] == {'type': 'activity', 'payload': {'type': 'long', 'response': "Computing ideal reminder time...done. Have a great dinner! We'll check in later.", 'concept': 'meal'}, 'raw': 'dinner'}

