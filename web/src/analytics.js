import ReactGA from 'react-ga';

ReactGA.initialize('UA-196778289-2', {cookieFlags: 'max-age=7200;SameSite=None;Secure'});

const shouldLogAnalytics = process.env.NODE_ENV.trim() === "production";
// console.log("initialized")

export const trackPatientPortalLoad = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Loaded homepage",
            value: userId
        });
    }
}

export const trackViewedDayDetails = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Viewed day details",
            value: userId
        });
    }
}

export const trackStartAddingDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Start adding dose window",
            value: userId
        });
    }
}

export const trackStartEditingDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Start editing dose window",
            value: userId
        });
    }
}

export const trackSubmitEditedDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Submit edited dose window",
            value: userId
        });
    }
}

export const trackStartDeletingDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Start deleting dose window",
            value: userId
        });
    }
}

export const trackSubmitDeletingDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Submit deleting dose window",
            value: userId
        });
    }
}

export const trackStartEditingHealthMetrics = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Start editing health metrics",
            value: userId
        });
    }
}

export const trackSubmitEditingHealthMetrics = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Submit editing health metrics",
            value: userId
        });
    }
}

export const trackPausedService = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Churn",
            action: "Paused service",
            value: userId
        });
    }
}

export const trackResumedService = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Growth",
            action: "Resumed service",
            value: userId
        });
    }
}