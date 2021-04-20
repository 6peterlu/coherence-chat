from freezegun import freeze_time
from datetime import datetime
from pytz import timezone
from nlp import segment_message, USER_TIMEZONE

@freeze_time("2000-01-01")
def test_segment_message():
    pacific_time = timezone(USER_TIMEZONE)
    assert segment_message("T")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}
    assert segment_message("T!")[0] == {'type': 'take', 'modifiers': {'emotion': 'excited'}, "raw": "T!"}
    assert segment_message("taken @ 12:15")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': pacific_time.localize(datetime(1999, 12, 31, 12, 15)), "raw": "taken @ 12:15"}
    assert segment_message("1")[0] == {'type': 'special', 'payload': '1', "raw": "1"}
    assert segment_message("1hr")[0] == {'type': 'requested_alarm_time', 'payload': pacific_time.localize(datetime(1999, 12, 31, 17, 0)), "raw": "1hr"}
    assert segment_message("1 hour")[0] == {'type': 'requested_alarm_time', 'payload': pacific_time.localize(datetime(1999, 12, 31, 17, 0)), "raw": "1 hour"}
    assert segment_message("2hr")[0] == {'type': 'requested_alarm_time', 'payload': pacific_time.localize(datetime(1999, 12, 31, 18, 0)), "raw": "2hr"}
    assert segment_message("10 min")[0] == {'type': 'requested_alarm_time', 'payload': pacific_time.localize(datetime(1999, 12, 31, 16, 10)), "raw": "10 min"}
    assert segment_message("20")[0] == {'type': 'delay_minutes', 'payload': 20, "raw": "20"}
    assert segment_message("T at 8:00")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': pacific_time.localize(datetime(1999, 12, 31, 8, 0)), "raw": "T at 8:00"}
    assert segment_message("T at 12:30")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': pacific_time.localize(datetime(1999, 12, 31, 12, 30)), "raw": "T at 12:30"}
    assert segment_message("T at 1:30pm")[0] == {'type': 'take', 'modifiers': {'emotion': 'neutral'}, 'payload': pacific_time.localize(datetime(1999, 12, 31, 13, 30)), "raw": "T at 1:30pm"}
    assert segment_message("2 on a walk")[0] == {'payload': '2', 'type': 'special', "raw": "2 on a walk"}
    assert segment_message("2 on a walk")[1] == {"payload": {"response": "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.", 'type': 'short'}, "type": "activity", "raw": "2 on a walk"}
    assert segment_message("T @ 0759")[0] == {'modifiers': {'emotion': 'neutral'}, 'payload': pacific_time.localize(datetime(1999, 12, 31, 7, 59)), "type": "take", "raw": "T @ 0759"}
    assert segment_message("T. Thanks!")[0] == {'modifiers': {'emotion': 'excited'}, 'type': 'take', "raw": "T. Thanks!"}
    assert segment_message("T. Thanks!")[1] == {'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}
    assert segment_message("Thank you! 5 minutes")[0] == {'type': 'requested_alarm_time', 'payload': pacific_time.localize(datetime(1999, 12, 31, 16, 5)), "raw": "Thank you! 5 minutes"}
    assert segment_message("Thank you! 5 minutes")[1] == {'type': 'thanks', 'modifiers': {'emotion': 'excited'}, "raw": "Thank you! 5 minutes"}
    assert segment_message("S :)")[0] == {'type': 'skip', "raw": "S :)"}