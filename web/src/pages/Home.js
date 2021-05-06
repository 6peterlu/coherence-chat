import React from "react";
import { useCookies } from 'react-cookie';
import { Redirect } from 'react-router-dom';
import { pullPatientData, pullPatientDataForNumber, updateDoseWindow } from '../api';
import Select from 'react-select';
import { Box, Button, Calendar, DropButton, Grid, Heading, Layer, Paragraph, Spinner } from "grommet";
import { CheckboxSelected, Close, FormNextLink } from "grommet-icons";
import { DateTime } from 'luxon';
import TimeInput from "../components/TimeInput"

const Home = () => {
    const [cookies, _, removeCookie] = useCookies(['token']);
    const [patientData, setPatientData] = React.useState(null);
    const [impersonateOptions, setImpersonateOptions] = React.useState([]);
    const [impersonating, setImpersonating] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [selectedDay, setSelectedDay] = React.useState(null);
    const [editingDoseWindow, setEditingDoseWindow] = React.useState(null);
    const [updatedDoseWindow, setUpdatedDoseWindow] = React.useState(null);

    const dateRange = [DateTime.local(2021, 5, 1), DateTime.local(2021, 5, 31)]

    React.useEffect(() => {
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

    const renderDay = React.useCallback(({date}) => {
        const dt = DateTime.fromJSDate(date);
        const day = dt.day;
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
    }, [patientData]);

    const nextDayConversion = (dt) => {
        if (dt.hour < 4) {
            return dt.plus({days: 1});
        }
        return dt;
    }

    const validDoseWindows = React.useMemo(() => {
        if (editingDoseWindow === null) {
            return true; // if you're not editing anything you're valid
        };
        if (patientData === null) {
            return true;  // if we have no patient data your dose windows are fine
        };
        const editingStartTime = nextDayConversion(DateTime.utc(2021, 5, 1, editingDoseWindow.start_hour, editingDoseWindow.start_minute).setZone("local").set({month: 5, day: 1}));
        const editingEndTime = nextDayConversion(DateTime.utc(2021, 5, 1, editingDoseWindow.end_hour, editingDoseWindow.end_minute).setZone("local").set({month: 5, day: 1}));
        for (const dw of patientData.doseWindows) {
            if (dw.id === editingDoseWindow.id) {
                continue;  // we don't compare to the one we're editing
            }
            const existingStartTime = nextDayConversion(DateTime.utc(2021, 5, 1, dw.start_hour, dw.start_minute).setZone("local").set({month: 5, day: 1}));
            const existingEndTime = nextDayConversion(DateTime.utc(2021, 5, 1, dw.end_hour, dw.end_minute).setZone("local").set({month: 5, day: 1}));
            if (editingStartTime <= existingStartTime && existingStartTime <= editingEndTime) {
                return false;
            }
            if (editingStartTime <= existingEndTime && existingEndTime <= editingEndTime) {
                return false;
            }
        }
        return true;
    }, [editingDoseWindow, patientData])

    // TODO: start here
    const renderDoseWindowEditFields = React.useCallback(() => {
        const startTime = DateTime.utc(2021, 5, 1, editingDoseWindow.start_hour, editingDoseWindow.start_minute);
        const endTime = DateTime.utc(2021, 5, 1, editingDoseWindow.end_hour, editingDoseWindow.end_minute);
        return (
            <>
                <TimeInput value={startTime.setZone('local')} onChangeTime={
                    (newTime) => {
                        const newDwTime = DateTime.local(2021, 5, 1, newTime.hour, newTime.minute).setZone("UTC");
                        setEditingDoseWindow({...editingDoseWindow, start_hour: newDwTime.hour, start_minute: newDwTime.minute});
                    }}
                />
                <TimeInput value={endTime.setZone('local')} onChangeTime={
                    (newTime) => {
                        const newDwTime = DateTime.local(2021, 5, 1, newTime.hour, newTime.minute).setZone("UTC");
                        setEditingDoseWindow({...editingDoseWindow, end_hour: newDwTime.hour, end_minute: newDwTime.minute});
                    }}
                />
                {<Button onClick={() => {updateDoseWindow(editingDoseWindow)}} label="Update" disabled={!validDoseWindows}/>}
            </>
        )
    }, [editingDoseWindow, validDoseWindows]);

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
                    <Box pad="medium" background={{color: "light-3"}}>
                        <Paragraph textAlign="center" margin={{vertical: "none"}}>Medication history</Paragraph>
                        <Calendar
                            date={(new Date()).toISOString()}
                            fill={true}
                            onSelect={(date) => {
                                const dt = DateTime.fromISO(date);
                                setSelectedDay(dt.day);
                            }}
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
                            <Box width="70vw" pad="large">
                                <Box direction="row" justify="between">
                                    <Paragraph size="large">May {selectedDay}</Paragraph>
                                    <Button icon={<Close />} onClick={() => setSelectedDay(false)} />
                                </Box>
                                {
                                    patientData.eventData[selectedDay - 1].day_status ?
                                    Object.keys(patientData.eventData[selectedDay - 1].time_of_day).map((key) => {
                                        return (
                                            <>
                                                <Paragraph key={`tod-${key}`}>{key} dose</Paragraph>
                                                <Box key={`todStatusContainer-${key}`} pad={{left: "medium"}}>
                                                    <Paragraph key={`todStatus-${key}`}>
                                                        {patientData.eventData[selectedDay - 1].time_of_day[key][0].type}{patientData.eventData[selectedDay - 1].time_of_day[key][0].time ? ` at ${DateTime.fromJSDate(new Date(patientData.eventData[selectedDay - 1].time_of_day[key][0].time)).toLocaleString(DateTime.TIME_SIMPLE)}` : ''}
                                                    </Paragraph>
                                                </Box>
                                            </>
                                        )
                                    }) :
                                    <Paragraph>No data for this day.</Paragraph>
                                }
                            </Box>
                        </Layer>
                    )}
                    <Box align="center">
                        <Paragraph textAlign="center" margin={{vertical: "none"}}>Dose windows</Paragraph>
                            {
                                patientData.doseWindows.map((dw) => {
                                    const startTime = DateTime.utc(2021, 5, 1, dw.start_hour, dw.start_minute);
                                    // startTime.set
                                    const endTime = DateTime.utc(2021, 5, 1, dw.end_hour, dw.end_minute);
                                    return (
                                        <Grid columns={["small", "xsmall"]} align="center" pad={{horizontal: "large"}} alignContent="center" justifyContent="center" justify="center">
                                            <Box direction="row" align="center">
                                                <Paragraph>{startTime.setZone('local').toLocaleString(DateTime.TIME_SIMPLE)}</Paragraph>
                                                <FormNextLink/>
                                                <Paragraph>{endTime.setZone('local').toLocaleString(DateTime.TIME_SIMPLE)}</Paragraph>
                                            </Box>
                                            <Button label="edit" onClick={() => setEditingDoseWindow(dw)}/>
                                        </Grid>
                                    )
                                })
                            }
                    </Box>
                    {editingDoseWindow && (
                        <Layer
                            onEsc={() => setEditingDoseWindow(null)}
                            onClickOutside={() => setEditingDoseWindow(null)}
                            responsive={false}
                        >
                            <Box width="90vw" pad="large">
                                <Box direction="row" justify="between">
                                    <Paragraph size="large">Edit dose window</Paragraph>
                                    <Button icon={<Close />} onClick={() => setEditingDoseWindow(null)} />
                                </Box>
                                <Box>
                                    {renderDoseWindowEditFields(editingDoseWindow)}
                                </Box>
                            </Box>
                        </Layer>
                    )}
                </>
            }

        </Box>
    )
}

export default Home;