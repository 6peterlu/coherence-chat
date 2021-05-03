import * as qs from 'query-string';
import Cookies from 'universal-cookie';

const cookies = new Cookies();

const apiServer = 'http://localhost:5000';

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
    headers.Authorization = token;
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
    headers.Authorization = token;
  }
  const fetchResult = await fetch(url, {
    method: 'get',
    headers,
  });
  if (fetchResult.ok) {
    const text = await fetchResult.text();
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