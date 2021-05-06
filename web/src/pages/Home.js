import React from "react";
import { useCookies } from 'react-cookie';
import { Redirect } from 'react-router-dom';
import { pullPatientData, pullPatientDataForNumber } from '../api';
import Select from 'react-select';
import { Box, Button, Calendar, DropButton, Grid, Heading, Layer, Paragraph, Spinner } from "grommet";
import { CheckboxSelected, Close } from "grommet-icons";
import { DateTime } from 'luxon';

const Home = () => {
    const [cookies, _, removeCookie] = useCookies(['token']);
    const [patientData, setPatientData] = React.useState(null);
    const [impersonateOptions, setImpersonateOptions] = React.useState([]);
    const [impersonating, setImpersonating] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [selectedDay, setSelectedDay] = React.useState(null);

    const dateRange = [DateTime.local(2021, 5, 1), DateTime.local(2021, 5, 31)]
    console.log(DateTime.local(2021, 5, 1).toString());

    React.useEffect(() => {
        console.log("running")
        const loadData = async () => {
            const loadedData = await pullPatientData();
            if (loadedData === null) {
                removeCookie("token");
                return;
            }
            setPatientData(loadedData);
            if (loadedData.impersonateList) {
                setImpersonateOptions(
                    loadedData.impersonateList.map((tuple_data) => { return { label: tuple_data[0], value: tuple_data[1]}})
                );
            }
            setLoading(false);
        }
        if (cookies.token && !patientData) {
            setLoading(true);
            loadData();
        }
    }, [cookies.token, removeCookie, patientData]);


    const loadDataForUser = async (selectedUser) => {
        const loadedData = await pullPatientDataForNumber(selectedUser.value);
        setPatientData(loadedData);
        setImpersonating(selectedUser.label);
    }

    const logout = () => {
        removeCookie("token");
    }

    const renderDay = ({date}) => {
        const dt = DateTime.fromJSDate(date);
        const day = dt.day;
        console.log(day);
        const dayOfMonthData = patientData.eventData[day - 1];
        let dayColor = null;
        if (dt.month === 5) {
            if (dayOfMonthData.day_status === "taken") {
                dayColor = "status-ok";
            } else if (dayOfMonthData.day_status === "missed") {
                dayColor = "status-error";
            } else if (dayOfMonthData.day_status === "missed") {
                dayColor = "status-warning";
            }
        }
        return (
            <Box align="center" justify="center">
                <Box width="30px" height="30px" round="medium" background={{color: dayColor}} align="center" justify="center">
                    <Paragraph>{day}</Paragraph>
                </Box>
            </Box>
        );
    }

    if (!cookies.token) {
        return <Redirect to="/login"/>;
    }

    return (
        // <>
        //     {cookies.token ? (<p>Logged in!</p>) : <Redirect to="/login"/>}
        //     <p>{JSON.stringify(patientData)}</p>
        //     <button onClick={logout}>Logout</button>
        //     {patientData.impersonateList ? <Select options={impersonateOptions} onChange={(selectedValue) => { loadDataForUser(selectedValue)}}/> : null}
        //     {impersonating ? <p>Impersonating {impersonating}</p> : null}
        // </>
        <Box>
            {loading ?
                <Spinner/>
                :
                <>
                    <Box align="center">
                        <Heading size="small">Good morning, Peter ☀️</Heading>
                    </Box>
                    <Box>
                        {true ?
                            <Box
                                align="center"
                                background={{"color":"status-warning", "dark": true}}
                                round="medium"
                                margin={{horizontal: "large"}}
                                pad={{vertical: "medium"}}
                                animation={{"type":"pulse","size":"medium","duration":2000}}
                            >
                                <Paragraph alignSelf="center" margin={{top: "none"}}>Dose to take now!</Paragraph>
                                <Box direction="row" justify="between" gap="medium">
                                    <Button label="Take" icon={<CheckboxSelected/>} primary/>
                                    <Button label="Skip"/>
                                </Box>
                            </Box>
                            :
                            <Box align="center" background={{"color":"status-ok", "dark": true}} round="medium" margin={{horizontal: "large"}}>
                                <Paragraph>You're all clear.</Paragraph>
                            </Box>
                        }
                    </Box>
                    <Box margin={{vertical: "medium"}} pad={{horizontal: "large"}}>
                        <DropButton
                            label="How do I use Coherence?"
                            dropContent={
                                <Box pad={{horizontal: "small"}}>
                                    <Paragraph textAlign="center">Texting commands</Paragraph>
                                    <Grid columns={["xsmall", "small"]}>
                                        <Paragraph size="small">T, taken</Paragraph>
                                        <Paragraph size="small">Mark your medication as taken at the current time</Paragraph>
                                        <Paragraph size="small">T @ 5:00pm</Paragraph>
                                        <Paragraph size="small">Mark your medication as taken at 5pm</Paragraph>
                                        <Paragraph size="small">S, skip</Paragraph>
                                        <Paragraph size="small">Skip the current dose</Paragraph>
                                        <Paragraph size="small">1</Paragraph>
                                        <Paragraph size="small">Delay the reminder by ten minutes</Paragraph>
                                        <Paragraph size="small">2</Paragraph>
                                        <Paragraph size="small">Delay the reminder by half an hour</Paragraph>
                                        <Paragraph size="small">3</Paragraph>
                                        <Paragraph size="small">Delay the reminder by an hour</Paragraph>
                                        <Paragraph size="small">20, 20 min</Paragraph>
                                        <Paragraph size="small">Delay the reminder by 20 minutes</Paragraph>
                                        <Paragraph size="small">W, website, site</Paragraph>
                                        <Paragraph size="small">Delay the reminder by 20 minutes</Paragraph>
                                        <Paragraph size="small">Eating, going for a walk</Paragraph>
                                        <Paragraph size="small">Tell Coherence you're busy with an activity</Paragraph>
                                        <Paragraph size="small">X</Paragraph>
                                        <Paragraph size="small">Report an error</Paragraph>
                                    </Grid>
                                </Box>
                            }
                            dropAlign={{ top: 'bottom' }}
                        />
                    </Box>
                    <Box pad={{horizontal: "medium"}}>
                        <Paragraph textAlign="center" margin={{vertical: "none"}}>Medication history</Paragraph>
                        <Calendar
                            date={(new Date()).toISOString()}
                            fill={true}
                            onSelect={setSelectedDay}
                            showAdjacentDays={true}
                            bounds={dateRange.map((date) => {return date.toString()})}
                            children={renderDay}
                        />
                    </Box>
                    {selectedDay && (
                        <Layer
                            onEsc={() => setSelectedDay(false)}
                            onClickOutside={() => setSelectedDay(false)}
                            responsive={false}
                        >
                            <Box margin="large">
                                <Button icon={<Close />} onClick={() => setSelectedDay(false)} />
                                <Paragraph>Selected day was {selectedDay}!</Paragraph>
                            </Box>
                        </Layer>
                    )}
                </>
            }

        </Box>
    )
}

export default Home;