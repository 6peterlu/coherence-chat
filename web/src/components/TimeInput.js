import React from "react";

import { Box, Select } from "grommet";

const TimeInput = ({value, onChangeTime}) => {
    const [hour, setHour] = React.useState(value.hour);
    const [minute, setMinute] = React.useState(value.minute);
    return (
        <Box direction="row">
            <Select options={[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]} value={hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour)} plain
                onChange={
                    ({value}) => {
                        let newHour = hour >= 12 ? value + 12 : value % 12;
                        setHour(newHour);
                        onChangeTime({hour: newHour, minute});
                    }
                }
            />
            <Select options={["00", "15", "30", "45"]} value={`${minute === 0 ? '0' : ''}${minute.toString()}`} plain onChange={({value}) => {
                setMinute(parseInt(value));
                onChangeTime({hour, minute: parseInt(value)});
            }}/>
            <Select options={["AM", "PM"]} value={hour >= 12 ? "PM" : "AM"} plain onChange={({value}) => {
                let newHour = hour;
                if (value === "AM") {
                    if (hour >= 12) {
                        newHour = hour - 12;
                        setHour(hour - 12);
                    }
                } else {
                    if (hour < 12) {
                        newHour = hour + 12;
                        setHour(hour + 12);
                    }
                }
                onChangeTime({hour: newHour, minute});
            }}/>
        </Box>
    )
}

export default TimeInput;