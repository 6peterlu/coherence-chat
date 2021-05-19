import React from "react";
import { useCookies } from 'react-cookie';
import { Redirect, useHistory } from 'react-router-dom';
import {
    deleteDoseWindow,
    pauseUser,
    pullPatientData,
    pullPatientDataForNumber,
    resumeUser,
    setHealthMetricsTracking,
    updateDoseWindow,
} from '../api';
import {
    trackStartAddingDoseWindow,
    trackPatientPortalLoad,
    trackViewedDayDetails,
    trackStartDeletingDoseWindow,
    trackStartEditingDoseWindow,
    trackStartEditingHealthMetrics,
    trackSubmitDeletingDoseWindow,
    trackSubmitEditedDoseWindow,
    trackSubmitEditingHealthMetrics,
    trackResumedService,
    trackPausedService
} from '../analytics';
import { Scatter } from 'react-chartjs-2';
import { Box, Button, CheckBoxGroup, Calendar, DropButton, Grid, Heading, Layer, Paragraph, Select } from "grommet";
import { Add, Checkmark, CircleInformation, Clear, Close, FormNextLink} from "grommet-icons";
import { DateTime } from 'luxon';
import 'chartjs-adapter-luxon';
import TimeInput from "../components/TimeInput";
import AnimatingButton from "../components/AnimatingButton";

const Home = () => {
    const [cookies, setCookie, removeCookie] = useCookies(['token']);
    const [patientData, setPatientData] = React.useState(null);
    const [calendarMonth, setCalendarMonth] = React.useState(5);
    const [impersonateOptions, setImpersonateOptions] = React.useState(null);
    const [impersonating, setImpersonating] = React.useState(null);
    const [selectedDay, setSelectedDay] = React.useState(null);
    const [editingDoseWindow, setEditingDoseWindow] = React.useState(null);
    const [deletingDoseWindow, setDeletingDoseWindow] = React.useState(null);
    const [editingHealthTracking, setEditingHealthTracking] = React.useState(null);
    const [timeRange, setTimeRange] = React.useState({label: "all time", value: null});
    const history = useHistory();
    console.log(timeRange);
    const [animating, setAnimating] = React.useState(false);  // this is setting animating for ALL buttons for now

    const dateRange = [DateTime.local(2021, 4, 1), DateTime.local(2021, 5, 31)]

    const loadData = React.useCallback(async () => {
        let loadedData = null;
        if (impersonating) {
            loadedData = await pullPatientDataForNumber(impersonating.value, calendarMonth);
        } else {
            loadedData = await pullPatientData(calendarMonth);
        };
        if (loadedData === null) {
            removeCookie("token");
            return;
        }
        console.log(loadedData);
        setPatientData(loadedData);
        if (loadedData.impersonateList === null) { // only track non impersonating data
            trackPatientPortalLoad(loadedData.patientId);
        }
        setCookie('token', loadedData.token, {secure: true});  // refresh login token
        if (loadedData.impersonateList) {
            setImpersonateOptions(
                loadedData.impersonateList.map((tuple_data) => { return { label: tuple_data[0], value: tuple_data[1]}})
            );
        }
        setAnimating(false);
    }, [calendarMonth, impersonating, removeCookie, setCookie])

    const shouldRerender = React.useMemo(() => {
        if (!cookies.token) {
            return false;
        }
        if (patientData === null) {
            return true;
        }
        if (patientData.month !== calendarMonth) {
            return true;
        }
        if (!!impersonating !== !! patientData.impersonating) {
            return true;
        }
        if (impersonating && patientData.impersonating && patientData.phoneNumber !== impersonating.value) {
            return true;
        }
        return false;
    }, [calendarMonth, cookies.token, impersonating, patientData]);

    React.useEffect(() => {
        console.log("rerendering")
        if (shouldRerender) {
            loadData();
        }
    }, [loadData, shouldRerender]);

    const logout = () => {
        removeCookie("token");
    }

    const renderDay = React.useCallback(({date}) => {
        let dayColor = null;
        const dt = DateTime.fromJSDate(date);
        const day = dt.day;
        if (patientData !== null) {
            if (patientData.eventData.length >= day) {
                const dayOfMonthData = patientData.eventData[day - 1];
                if (dt.month === calendarMonth) {
                    if (dayOfMonthData.day_status === "taken") {
                        dayColor = "status-ok";
                    } else if (dayOfMonthData.day_status === "missed") {
                        dayColor = "status-error";
                    } else if (dayOfMonthData.day_status === "skip") {
                        dayColor = "status-warning";
                    }
                }
            }
        }
        return (
            <Box align="center" justify="center" margin={{vertical: "xsmall"}}>
                <Box width="30px" height="30px" round="medium" background={{color: dayColor}} align="center" justify="center">
                    <Paragraph>{day}</Paragraph>
                </Box>
            </Box>
        );
    }, [calendarMonth, patientData]);

    const formattedHealthMetricData = React.useMemo(() => {
        const units = {
            weight: "pounds",
            glucose: "mg/dL",
            "blood pressure": "mm/hg"
        }
        const data = {}
        if (patientData !== null) {
            for (const metric in patientData.healthMetricData) {
                const metric_list = patientData.healthMetricData[metric];
                console.log(metric_list);
                if (metric !== "blood pressure") {
                    data[metric] = {
                        datasets: [{
                            data: metric_list.map((metric) => {
                                const jsTime = DateTime.fromHTTP(metric.time);
                                return {x: jsTime, y: metric.value};
                            }),
                            label: metric,
                            fill: false,
                            backgroundColor: 'rgb(255, 99, 132)',
                            borderColor: 'rgba(255, 99, 132, 0.2)'
                        }], options:{
                                scales: {
                                    x: {
                                        type: "time",
                                        time: {unit: "day"},
                                        grid: {"color": ["#777"]},
                                        ticks:{color: "#FFF"},
                                        min: timeRange.value !== null ? DateTime.local().minus({days: timeRange.value}).toISODate() : null},
                                    y: {grid: {"color": ["#AAA"]}, ticks:{color: "#FFF"}, title: {text:units[metric], display: true, color: "#FFF"}}
                                },
                                color: "white",
                                plugins: {
                                    legend: {display: false},
                                },
                                elements: {
                                    point: {
                                        hitRadius: 10,
                                        hoverRadius: 10
                                    }
                                },
                                showLine: true
                        }
                    };
                } else { // blood pressure has two timeseries
                    data[metric] = {
                        datasets: [
                        {
                            data: metric_list.map((metric) => {
                                const jsTime = DateTime.fromHTTP(metric.time);
                                return {x: jsTime, y: metric.value.systolic};
                            }),
                            label: "systolic",
                            fill: false,
                            backgroundColor: 'rgb(255, 99, 132)',
                            borderColor: 'rgba(255, 99, 132, 0.2)'
                        },
                        {
                            data: metric_list.map((metric) => {
                                const jsTime = DateTime.fromHTTP(metric.time);
                                return {x: jsTime, y: metric.value.diastolic};
                            }),
                            label: "diastolic",
                            fill: false,
                            backgroundColor: 'rgb(99, 255, 132)',
                            borderColor: 'rgba(99, 255, 132, 0.2)'
                        }
                    ], options:{
                        scales: {
                            x: {
                                type: "time",
                                time: {unit: "day"},
                                grid: {"color": ["#777"]},
                                ticks:{color: "#FFF"},
                                min: timeRange.value !== null ? DateTime.local().minus({days: timeRange.value}).toISODate() : null
                            },
                            y: {grid: {"color": ["#AAA"]}, ticks:{color: "#FFF"}, title: {text:units[metric], display: true, color: "#FFF"}}
                        },

                        color: "white",
                        plugins: {
                            datalabels: {color: 'black'}
                        },
                        elements: {
                            point: {
                                hitRadius: 10,
                                hoverRadius: 10
                            }
                        },
                        showLine: true
                    }
                    };
                }
            }
        }
        console.log("returned HM data:")
        console.log(data);

        return data;
    }, [patientData, timeRange]);

    const renderImpersonateListItem = React.useCallback((listItem) => {
        console.log(listItem);
        return listItem.label;
    }, [])

    const nextDayConversion = (dt) => {
        if (dt.hour < 4) {
            return dt.plus({days: 1});
        }
        return dt;
    }

    const validDoseWindows = React.useMemo(() => {
        console.log("recomputing")
        if (editingDoseWindow === null) {
            return true; // if you're not editing anything you're valid
        };
        if (patientData === null) {
            return true;  // if we have no patient data your dose windows are fine
        };
        const editingStartTime = nextDayConversion(DateTime.utc(2021, 5, 1, editingDoseWindow.start_hour, editingDoseWindow.start_minute).setZone("local").set({month: 5, day: 1}));
        const editingEndTime = nextDayConversion(DateTime.utc(2021, 5, 1, editingDoseWindow.end_hour, editingDoseWindow.end_minute).setZone("local").set({month: 5, day: 1}));
        if (editingEndTime < editingStartTime.plus({minutes: 30})) {
            return false; // dose window is too short
        }
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
    }, [editingDoseWindow, patientData]);

    const currentTimeOfDay = React.useMemo(() => {
        const currentTime = DateTime.local();
        if (currentTime.hour > 4 && currentTime.hour < 12) {
            return "morning";
        } else if (currentTime.hour > 12 && currentTime.hour < 18) {
            return "afternoon";
        } else {
            return "evening"
        }
    }, []);

    const dateToDisplay = React.useMemo(() => {
        const currentDay = DateTime.local();
        if (calendarMonth === currentDay.month) {
            return currentDay;
        } else {
            return currentDay.set({month: calendarMonth, day: 1});
        }
    }, [calendarMonth])

    const randomChoice = (arr) => {
        return arr[Math.floor(arr.length * Math.random())];
    }
    const randomHeaderEmoji = React.useMemo(() =>  {
        return randomChoice(["💫", "🌈", "🌱", "🏆", "📈", "💎", "💡", "🔆", "🔔"]);
    }, [])

    const renderDoseWindowEditFields = React.useCallback(() => {
        if (patientData === null) {
            return null;
        }
        const startTime = DateTime.utc(2021, 5, 1, editingDoseWindow.start_hour, editingDoseWindow.start_minute);
        const endTime = DateTime.utc(2021, 5, 1, editingDoseWindow.end_hour, editingDoseWindow.end_minute);
        return (
            <>
                <Paragraph size="small" margin={{bottom: "none"}}>Start time (earliest time you'll be reminded)</Paragraph>
                <TimeInput value={startTime.setZone('local')} color="dark-3" onChangeTime={
                    (newTime) => {
                        const newDwTime = DateTime.local(2021, 5, 1, newTime.hour, newTime.minute).setZone("UTC");
                        setEditingDoseWindow({...editingDoseWindow, start_hour: newDwTime.hour, start_minute: newDwTime.minute});
                    }}
                />
                <Paragraph size="small" margin={{bottom: "none"}}>End time (latest time you'll be reminded)</Paragraph>
                <TimeInput value={endTime.setZone('local')} color="dark-3" onChangeTime={
                    (newTime) => {
                        console.log(`changed time to ${JSON.stringify(newTime)}`)
                        const newDwTime = DateTime.local(2021, 5, 1, newTime.hour, newTime.minute).setZone("UTC");
                        setEditingDoseWindow({...editingDoseWindow, end_hour: newDwTime.hour, end_minute: newDwTime.minute});
                    }}
                />
                {<AnimatingButton
                    onClick={async () => {
                        setAnimating(true);
                        console.log("set animating");
                        await updateDoseWindow(editingDoseWindow);
                        await loadData();
                        setEditingDoseWindow(null);
                        if (impersonateOptions === null) {
                            trackSubmitEditedDoseWindow(patientData.patientId);
                        }
                    }}
                    label={validDoseWindows ? editingDoseWindow.id ? "Update" : "Create" : "Invalid dose window"}
                    disabled={!validDoseWindows}
                    animating={animating}
                />}
                {editingDoseWindow.id ? <AnimatingButton onClick={() => {
                    setDeletingDoseWindow(editingDoseWindow);
                    if (impersonateOptions === null) {
                        trackStartDeletingDoseWindow(patientData.patientId);
                    }
                }}
                    disabled={animating}
                    size="small"
                    padding={{horizontal: "none"}}
                    margin={{top: "medium"}}
                    label="Delete dose window"
                    color="status-error"
                    plain={true}
                    alignSelf="center"
                /> : null}
            </>
        )
    }, [animating, editingDoseWindow, impersonateOptions, loadData, patientData, validDoseWindows]);

    if (!cookies.token) {
        return <Redirect to="/login"/>;
    }
    if (patientData !== null && ["payment_method_requested", "subscription_expired"].includes(patientData.state)) {
        return <Redirect to="/payment"/>
    }
    if (patientData !== null && ["intro", "dose_windows_requested", "dose_window_times_requested", "timezone_requested"].includes(patientData.state)) {
        return <Redirect to="/finishOnboarding"/>
    }

    const orderDays = (t1, t2) => {
        if (t1 === t2) {
            return 0;
        }
        if (t1 === "morning" || (t1 === "afternoon" && t2 === "evening")) {
            return -1;
        }
        return 1;
    }

    console.log(timeRange.label);
    return (
        <Box>
            {impersonateOptions !== null ?
                <Box direction="row" align="center" gap="small" pad={{"horizontal": "medium"}}>
                    <Paragraph>Impersonating:</Paragraph>
                    <Select
                        options={impersonateOptions}
                        children={renderImpersonateListItem}
                        onChange={({option}) => {
                            console.log("setting");
                            setImpersonating(option);
                        }}
                    />
                </Box> : null}
            <Box align="center">
                <Heading size="small">Good {currentTimeOfDay}{patientData ? `, ${patientData.patientName}` : ""}.</Heading>
            </Box>
            <Box>
                {patientData && patientData.takeNow ?
                    <Box
                        align="center"
                        background={{"color":"status-warning", "dark": true}}
                        round="medium"
                        margin={{horizontal: "large"}}
                        pad={{vertical: "medium"}}
                        animation={{"type":"pulse","size":"medium","duration":2000}}
                    >
                        <Paragraph alignSelf="center" margin={{vertical: "none"}}>Dose to take now!</Paragraph>
                    </Box>
                    :
                    <Box align="center" background={{"color":"brand", "dark": true}} round="medium" margin={{horizontal: "large"}}>
                        <Paragraph>No doses to take right now. {randomHeaderEmoji}</Paragraph>
                    </Box>
                }
            </Box>
            <Box margin={{vertical: "medium"}} pad={{horizontal: "large"}}>
                <DropButton
                    icon={<CircleInformation/>}
                    label="How do I use Coherence?"
                    dropContent={
                        <Box pad={{horizontal: "small"}}>
                            <Paragraph textAlign="center">Texting commands</Paragraph>
                            <Grid columns={["xsmall", "small"]} align="center" justifyContent="center" gap={{column: "small"}}>
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
                                <Paragraph size="small">glucose:140, 140 mg/dL</Paragraph>
                                <Paragraph size="small">Record glucose reading</Paragraph>
                                <Paragraph size="small">weight:150, 150 pounds, 150 lb</Paragraph>
                                <Paragraph size="small">Record weight reading</Paragraph>
                                <Paragraph size="small">120/80, 120 80</Paragraph>
                                <Paragraph size="small">Record blood pressure reading</Paragraph>
                                <Paragraph size="small">W, website, site</Paragraph>
                                <Paragraph size="small">Get the website link sent to you</Paragraph>
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
                <Paragraph textAlign="center" margin={{vertical: "none"}} fill={true}>Medication history</Paragraph>
                <Calendar
                    date={dateToDisplay.toISO()}
                    fill={true}
                    onSelect={(date) => {
                        const dt = DateTime.fromISO(date);
                        setSelectedDay(dt.day);
                        if (impersonateOptions === null) {
                            trackViewedDayDetails(patientData.patientId);
                        }
                    }}
                    showAdjacentDays={false}
                    bounds={dateRange.map((date) => {return date.toString()})}
                    children={renderDay}
                    daysOfWeek={true}
                    onReference={(date) => {
                        setCalendarMonth(DateTime.fromISO(date).month);
                        setPatientData({...patientData, eventData: []}); // hide event data while we load
                    }}
                    animate={false}
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
                            <Paragraph size="large">{DateTime.local().set({month: calendarMonth}).monthLong} {selectedDay}</Paragraph>
                            <Button icon={<Close />} onClick={() => setSelectedDay(false)} />
                        </Box>
                        {
                            patientData.eventData[selectedDay - 1].day_status ?
                            Object.keys(patientData.eventData[selectedDay - 1].time_of_day).sort(orderDays).map((key) => {
                                let numberSuffix = patientData.eventData[selectedDay - 1].time_of_day[key].length > 1;  // handle multiple dose windows in the same time of day
                                return (
                                    patientData.eventData[selectedDay - 1].time_of_day[key].map((event, index) => {
                                        return (
                                            <>
                                                <Paragraph key={`tod-${key}`} margin={{bottom: "none"}}>{key} dose{numberSuffix ? ` ${index + 1}` : ''}</Paragraph>
                                                <Box key={`todStatusContainer-${key}`} pad={{left: "medium"}} direction="row" align="center" justify="between">
                                                    <Paragraph key={`todStatus-${key}`} size="small">
                                                        {event.type}{event.time ? ` at ${DateTime.fromJSDate(new Date(event.time)).toLocaleString(DateTime.TIME_SIMPLE)}` : ''}
                                                    </Paragraph>
                                                    {event.type === "taken" ? <Checkmark color="status-ok" size="small"/> : null}
                                                    {event.type === "skipped" ? <Clear color="status-warning" size="small"/> : null}
                                                    {event.type === "missed" ? <Close color="status-error" size="small"/> : null}
                                                </Box>
                                            </>
                                        )
                                    })
                                )
                            }) :
                            <Paragraph>No data for this day.</Paragraph>
                        }
                    </Box>
                </Layer>
            )}
            <Box align="center" background="brand" pad={{bottom: "large"}}>
                <Paragraph margin={{bottom: "none"}}>Health tracking</Paragraph>
                {Object.keys(formattedHealthMetricData).length === 0 ?
                    <>
                        <Paragraph size="small">You're not tracking any health metrics yet.</Paragraph>
                        <Paragraph size="small" textAlign="center">Tracking is a brand new feature that allows you to text us health data such as blood pressure, weight, or glucose. You can then view your historical data here at any time.</Paragraph>
                    </>
                : null}
                {Object.keys(formattedHealthMetricData).length !== 0 ?
                <Box margin={{top: "small"}}>
                    <Select
                        options={[{label: "week", value: 7}, {label: "month", value: 30}, {label: "3 months", value: 90}, {label: "year", value: 365}, {label: "all time", value: null}]}
                        children={(option) => {return <Paragraph margin="small">{option.label}</Paragraph>}}
                        onChange={({value}) => { setTimeRange(value)}}
                        valueLabel={<Paragraph margin={{vertical: "xsmall", horizontal: "small"}}>{timeRange.label}</Paragraph>}
                        // labelKey="label"
                    />
                </Box> : null}
                {formattedHealthMetricData && "blood pressure" in formattedHealthMetricData ? (
                    <Box pad={{horizontal: "large"}} fill="horizontal">
                        <Paragraph size="small" margin={{bottom: "none"}}>Blood pressure</Paragraph>
                        {formattedHealthMetricData["blood pressure"].datasets[0].data.length > 0 ?
                            <Scatter data={{datasets: formattedHealthMetricData["blood pressure"].datasets}} options={formattedHealthMetricData["blood pressure"].options}/> :
                            <Paragraph alignSelf="center" size="small">No blood pressure data recorded yet. Example texts you can send: "120/80", "120 80".</Paragraph>
                        }
                    </Box>) : null}
                {formattedHealthMetricData && "weight" in formattedHealthMetricData ?
                    <Box pad={{horizontal: "large"}} fill="horizontal">
                        <Paragraph size="small" margin={{bottom: "none"}}>Weight</Paragraph>
                        {formattedHealthMetricData.weight.datasets[0].data.length > 0 ?
                        <Scatter data={{datasets: formattedHealthMetricData.weight.datasets}} options={formattedHealthMetricData.weight.options}/> :
                        <Paragraph alignSelf="center" size="small">No weight data recorded yet. Example texts you can send: "weight:150", "150 lb", "150 pounds".</Paragraph>}
                    </Box>
                    : null}
                {formattedHealthMetricData && "glucose" in formattedHealthMetricData ?
                    <Box pad={{horizontal: "large"}} fill="horizontal">
                        <Paragraph size="small" margin={{bottom: "none"}}>Glucose</Paragraph>
                        {formattedHealthMetricData.glucose.datasets[0].data.length > 0 ?
                        <Scatter data={{datasets: formattedHealthMetricData.glucose.datasets}} options={formattedHealthMetricData.glucose.options}/> :
                        <Paragraph alignSelf="center" size="small">No glucose data recorded yet. Example texts you can send: "glucose:140", "140 mg/dL"</Paragraph>}
                    </Box>
                    : null}
                <Button label={Object.keys(formattedHealthMetricData).length === 0 ? "Start tracking": "Edit tracking"} onClick={() => {
                    setEditingHealthTracking(Object.keys(formattedHealthMetricData));
                    if (impersonateOptions === null) {
                        trackStartEditingHealthMetrics(patientData.patientId);
                    }
                }} margin={{top: "medium"}}/>
            </Box>
            {editingHealthTracking !== null ?
                <Layer
                    onEsc={() => setEditingHealthTracking(null)}
                    onClickOutside={() => setEditingHealthTracking(null)}
                    responsive={false}
                >
                    <Box width="70vw" pad="large">
                        <Box direction="row" justify="between">
                            <Paragraph size="large">Choose what you want to track</Paragraph>
                            <Button icon={<Close />} onClick={() => setEditingHealthTracking(null)} />
                        </Box>
                        <CheckBoxGroup
                            options={["blood pressure", "weight", "glucose"]}
                            value={editingHealthTracking}
                            onChange={(e) => {setEditingHealthTracking(e.value)}}
                        />
                        <AnimatingButton animating={animating} label="Save changes" margin={{top:"medium"}} onClick={async () => {
                            setAnimating(true);
                            console.log(editingHealthTracking);
                            await setHealthMetricsTracking(editingHealthTracking);
                            await loadData();
                            setEditingHealthTracking(null);
                            if (impersonateOptions === null) {
                                trackSubmitEditingHealthMetrics(patientData.patientId);
                            }
                        }}/>
                    </Box>
                </Layer> : null
            }
            <Box align="center" pad={{vertical: "medium"}} margin={{horizontal: "xlarge"}} border="bottom">
                <Paragraph textAlign="center" margin={{vertical: "none"}}>Dose windows</Paragraph>
                    {
                        patientData ? patientData.doseWindows.map((dw) => {
                            const startTime = DateTime.utc(2021, 5, 1, dw.start_hour, dw.start_minute);
                            const endTime = DateTime.utc(2021, 5, 1, dw.end_hour, dw.end_minute);
                            return (
                                <Grid key={`doseWindowContainer-${dw.id}`} columns={["small", "flex", "flex"]} align="center" pad={{horizontal: "large"}} alignContent="center" justifyContent="center" justify="center">
                                    <Box direction="row" align="center">
                                        <Paragraph>{startTime.setZone('local').toLocaleString(DateTime.TIME_SIMPLE)}</Paragraph>
                                        <FormNextLink/>
                                        <Paragraph>{endTime.setZone('local').toLocaleString(DateTime.TIME_SIMPLE)}</Paragraph>
                                    </Box>
                                    <Button label="edit" onClick={() => {
                                        setEditingDoseWindow(dw);
                                        if (impersonateOptions === null) {
                                            trackStartEditingDoseWindow(patientData.patientId);
                                        }
                                    }} size="small" margin={{horizontal: "none"}}/>
                                </Grid>
                            )
                        }) : null
                    }
                    <Button label="Add dose window" onClick={() => {
                        setEditingDoseWindow({start_hour: 0, start_minute:0, end_hour: 0, end_minute: 0});
                        if (impersonateOptions === null) {
                            trackStartAddingDoseWindow(patientData.patientId);
                        }
                    }} icon={<Add/>}/>
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
            {deletingDoseWindow && (
                <Layer
                    onEsc={() => setDeletingDoseWindow(null)}
                    onClickOutside={() => setDeletingDoseWindow(null)}
                    responsive={false}
                >
                    <Box width="90vw" pad="large">
                        <Box direction="row" justify="between">
                            <Paragraph size="large">Confirm delete dose window</Paragraph>
                            <Button icon={<Close />} onClick={() => setDeletingDoseWindow(null)}/>
                        </Box>
                        <Box align="center">
                            <Paragraph margin={{bottom: "none"}}>You're about to delete the dose window</Paragraph>
                            <Box direction="row" align="center" margin={{bottom: "medium"}}>
                                <Paragraph>{DateTime.utc(2021, 5, 1, deletingDoseWindow.start_hour, deletingDoseWindow.start_minute).setZone('local').toLocaleString(DateTime.TIME_SIMPLE)}</Paragraph>
                                <FormNextLink/>
                                <Paragraph>{DateTime.utc(2021, 5, 1, deletingDoseWindow.end_hour, deletingDoseWindow.end_minute).setZone('local').toLocaleString(DateTime.TIME_SIMPLE)}</Paragraph>
                            </Box>
                            <AnimatingButton onClick={async () => {
                                setAnimating(true);
                                await deleteDoseWindow(deletingDoseWindow.id)
                                await loadData();
                                setDeletingDoseWindow(null);
                                setEditingDoseWindow(null);
                                if (impersonateOptions === null) {
                                    trackSubmitDeletingDoseWindow(patientData.patientId);
                                }
                            }} label="Confirm" animating={animating}/>
                        </Box>
                    </Box>
                </Layer>
            )}
            <Box align="center" pad={{vertical: "medium"}}>
                {patientData ?
                <>
                    <Paragraph textAlign="center" margin={{vertical: "none"}}>Pause / resume Coherence</Paragraph>
                    <Paragraph size="small" color="dark-3">Coherence is currently {patientData.pausedService ? "paused" : "active"}.</Paragraph>
                    <AnimatingButton
                        background={patientData.pausedService ? {"dark": true} : null}
                        animating={animating}
                        style={{padding: "10px"}}
                        primary={patientData.pausedService}
                        onClick={async () => {
                            setAnimating(true);
                            if (patientData.pausedService) {
                                await resumeUser();
                                if (impersonateOptions === null) {
                                    trackResumedService(patientData.patientId);
                                }
                            } else {
                                await pauseUser();
                                if (impersonateOptions === null) {
                                    trackPausedService(patientData.patientId);
                                }
                            }
                            loadData();
                        }} label={`${patientData.pausedService ? "Resume" : "Pause"} Coherence`} />
                    {patientData.pausedService ? <Paragraph size="small" color="status-warning" textAlign="center">While Coherence is paused, we can't respond to any texts you send us, or remind you about your medications.</Paragraph> : null}
                </> : null}
            </Box>
            <Box align="center" pad={{vertical: "medium"}} margin={{horizontal: "xlarge"}} border="top">
                <Paragraph textAlign="center" margin={{vertical: "none"}}>Need help with anything?</Paragraph>
                <Paragraph size="small" color="dark-3">Our customer service is just a text away at (650) 667-1146. Reach out any time and we'll get back to you in a few hours!</Paragraph>
            </Box>
            <Box align="center" pad={{vertical: "medium"}} margin={{horizontal: "xlarge"}} border="top" direction="row" justify={impersonateOptions ? "between" : "center"}>
                {impersonateOptions ? <Button onClick={() => {history.push("/payment")}} label="Manage subscription" size="small"/> : null}
                <Button onClick={logout} label="Log out" size="small"/>
            </Box>
        </Box>
    )
}

export default Home;