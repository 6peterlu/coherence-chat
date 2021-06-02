import ReactGA from 'react-ga';

ReactGA.initialize('UA-196778289-2', {cookieFlags: 'max-age=7200;SameSite=None;Secure'});

const shouldLogAnalytics = process.env.NODE_ENV.trim() === "production";

export const trackPatientPortalLoad = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Loaded homepage",
            label: userId
        });
    }
}

export const trackViewedDayDetails = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Viewed day details",
            label: userId
        });
    }
}

export const trackStartAddingDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Start adding dose window",
            label: userId
        });
    }
}

export const trackStartEditingDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Start editing dose window",
            label: userId
        });
    }
}

export const trackSubmitEditedDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Submit edited dose window",
            label: userId
        });
    }
}

export const trackStartDeletingDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Start deleting dose window",
            label: userId
        });
    }
}

export const trackSubmitDeletingDoseWindow = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Submit deleting dose window",
            label: userId
        });
    }
}

export const trackStartEditingHealthMetrics = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Start editing health metrics",
            label: userId
        });
    }
}

export const trackSubmitEditingHealthMetrics = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Engagement",
            action: "Submit editing health metrics",
            label: userId
        });
    }
}

export const trackPausedService = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Churn",
            action: "Paused service",
            label: userId
        });
    }
}

export const trackResumedService = (userId) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Growth",
            action: "Resumed service",
            label: userId
        });
    }
}


export const trackLandingPageSignup = (phoneNumber) => {
    if (shouldLogAnalytics) {
        ReactGA.event({
            category: "Growth",
            action: "Signed up on landing page",
            label: phoneNumber
        });
    }
}