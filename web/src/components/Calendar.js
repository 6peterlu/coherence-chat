// import React from "react";
// import { Grid, Paragraph } from "grommet";

// const CALENDAR_DATA = {
//     "May": {
//         firstDay: 6,
//         daysInMonth: 31
//     }
// };

// const Calendar = ({month, popupComponent}) => {
//     const {firstDay, daysInMonth} = CALENDAR_DATA[month];
//     const totalDaysNeeded = Math.ceil((firstDay + daysInMonth) / 7) * 7;
//     return (
//         <Grid columns="min" rows="xsmall">
//             {[...Array(totalDaysNeeded).keys()].map(
//                 (idx) => {
//                     if (idx < firstDay) {
//                         return <Paragraph>{idx + 1}</Paragraph>
//                     } else if (idx < firstDay + daysInMonth + 1) {
//                         return <Paragraph>{idx - firstDay}</Paragraph>
//                     } else {
//                         return <Paragraph>{idx - firstDay - daysInMonth + 1}</Paragraph>
//                     }
//                 }
//             )}
//         </Grid>
//     );
// }

// export default Calendar;