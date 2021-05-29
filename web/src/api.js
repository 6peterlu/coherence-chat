import * as qs from 'query-string';
import Cookies from 'universal-cookie';

const cookies = new Cookies();

console.log(process.env.NODE_ENV);
const apiServer = process.env.NODE_ENV.trim() === "production" ? "https://coherence-chat.herokuapp.com" : 'http://localhost:5000';

const post = async (route, payload) => {
  const token = cookies.get('token');
  const headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    "Access-Control-Allow_Methods": "POST",
    "Access-Control_Allow_Headers": "*",
    "Access-Control-Allow-Origin": "*",
  };
  if (token) {
    headers.Authorization = 'Basic ' + btoa(token + ":unused");
  }
  const fetchResult = await fetch(`${apiServer}/${route}`, {
    method: 'post',
    headers,
    body: JSON.stringify(payload),
  });

  if (fetchResult.ok) {
    const text = await fetchResult.text();
    return JSON.parse(text);
  }
  console.log(
    `POST call to /${route} errored with status ${fetchResult.status}`,
  );
  return null;
};

const get = async (route, params) => {
  let url = `${apiServer}/${route}`;
  url += `?${qs.stringify(params)}`;

  const token = cookies.get('token');
  const headers = {
    Accept: 'application/json',
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Origin": "*",
  };
  if (token) {
    headers.Authorization = 'Basic ' + btoa(token + ":unused");
  }
  const fetchResult = await fetch(url, {
    method: 'get',
    headers,
  });
  if (fetchResult.ok) {
    const text = await fetchResult.text();
    console.log(text);
    return JSON.parse(text);
  }
  console.log(
    `GET call to /${route} errored with status ${fetchResult.status}`,
  );
  return null;
};

export const login = async (phoneNumber, secretCode, password) => {
    const response = await post("login/new", { phoneNumber, secretCode, password });
    return response;
}

export const pullPatientData = async (calendarMonth) => {
  const response = await get("patientData/new", { calendarMonth });
  return response;
}

export const pullPatientDataForNumber = async (phoneNumber, calendarMonth) => {
  const response = await get("patientData/new", { phoneNumber, calendarMonth });
  return response;
}

export const pullPatientPaymentData = async () => {
  console.log("calling this at least?")
  const response = await get("user/getPaymentData", {});
  return response;
}

export const updateDoseWindow = async (updatedDoseWindow) => {
  const response = await post("doseWindow/update/new", { updatedDoseWindow });
  return response;
}

export const deleteDoseWindow = async (dwId) => {
  const response = await post("doseWindow/deactivate/new", { doseWindowId: dwId });
  return response;
}

export const pauseUser = async () => {
  const response = await post("user/pause/new");
  return response;
}

export const resumeUser = async () => {
  const response = await post("user/resume/new");
  return response;
}

export const setHealthMetricsTracking = async (metricList) => {
  const response = await post("user/healthMetrics/set", { metricList });
  return response;
}

export const submitPaymentInfo = async () => {
  const response = await post("user/submitPaymentInfo", {});
  return response;
}

export const cancelSubscription = async () => {
  console.log("attempting to cancel sub");
  const response = await post("user/cancelSubscription", {});
  return response;
}

export const renewSubscription = async () => {
  const response = await post("user/renewSubscription", {});
  return response;
}

export const landingPageSignup = async (name, email, phoneNumber, trialCode) => {
  const response = await post("user/landingPageSignup", {
    name, email, phoneNumber, trialCode
  });
  return response;
}

export const getPatientState = async () => {
  const response = await get("patientState",  {});
  return response;
}

export const getUserProfile = async () => {
  const response = await get("user/profile", {});
  return response;
}

// TODO: only submit timezone
export const updateUserTimezone = async (userData) => {
  const response = await post("user/updateTimezone", userData);
  return response;
}

export const updateUserPassword = async (password) => {
  const response = await post("user/password", { password });
  return response;
}