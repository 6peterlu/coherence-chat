import { DateTime } from 'luxon';

export const getCurrentStandardTimezone = () => {
    const localTime = DateTime.local();
    let localTimeOffset = localTime.offset;
    if (localTime.isInDST) {
        localTimeOffset -= 60;
    }
    if (localTimeOffset === -480) {
        return "US/Pacific";
    } else if (localTimeOffset === -420) {
        return "US/Mountain";
    } else if (localTimeOffset === -360) {
        return "US/Central";
    } else if (localTimeOffset === -300) {
        return "US/Eastern";
    } else {
        return null;
    }
}

// accepts luxon dt object
export const daysUntilDate = (dt) => {
    const currentTime = DateTime.local();
    return Math.floor(dt.diff(currentTime, 'days').days);
}