import ReactGA from 'react-ga';

ReactGA.initialize('UA-196778289-2', {cookieFlags: 'max-age=7200;SameSite=None;Secure'});
// console.log("initialized")

export const trackPatientPortalLoad = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Loaded homepage",
        value: userId
    });
}

export const trackViewedDayDetails = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Viewed day details",
        value: userId
    });
}

export const trackStartAddingDoseWindow = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Start adding dose window",
        value: userId
    });
}

export const trackStartEditingDoseWindow = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Start editing dose window",
        value: userId
    });
}

export const trackSubmitEditedDoseWindow = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Submit edited dose window",
        value: userId
    });
}

export const trackStartDeletingDoseWindow = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Start deleting dose window",
        value: userId
    });
}

export const trackSubmitDeletingDoseWindow = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Submit deleting dose window",
        value: userId
    });
}

export const trackStartEditingHealthMetrics = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Start editing health metrics",
        value: userId
    });
}

export const trackSubmitEditingHealthMetrics = (userId) => {
    ReactGA.event({
        category: "Engagement",
        action: "Submit editing health metrics",
        value: userId
    });
}

export const trackPausedService = (userId) => {
    ReactGA.event({
        category: "Churn",
        action: "Paused service",
        value: userId
    });
}

export const trackResumedService = (userId) => {
    ReactGA.event({
        category: "Growth",
        action: "Resumed service",
        value: userId
    });
}