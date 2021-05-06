import React from "react";

import { MaskedInput } from "grommet";

const TimeInput = ({value, onChangeTime}) => {
    return  <MaskedInput
        mask={[
            {
            length: [1, 2],
            options: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
            regexp: /^1[1-2]$|^[0-9]$/,
            placeholder: 'hh',
            },
            { fixed: ':' },
            {
            length: 2,
            options: ['00', '15', '30', '45'],
            regexp: /^[0-5][0-9]$|^[0-9]$/,
            placeholder: 'mm',
            },
            { fixed: ' ' },
            {
            length: 2,
            options: ['am', 'pm'],
            regexp: /^[ap]m$|^[AP]M$|^[aApP]$/,
            placeholder: 'ap',
            },
        ]}
        value={value}
        onChange={(e) => {
            const rawString = e.target.value;
            let hour = parseInt(value.split(":")[0]);
            const minute = parseInt(value.split(":")[1].slice(0,2));
            if (rawString.includes("pm")) {
                hour += 12;
            }
            onChangeTime({ hour, minute });
        }}
    />
}

export default TimeInput;