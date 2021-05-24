import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { CookiesProvider } from 'react-cookie';
import { Grommet } from "grommet";

const grommetTheme = {
  global: {
    colors: {
      brand: "#002864",
      text: {light: "#002864"},
      paragraph: {light: "#002864"},
      background: "#FFF"
    },
    breakpoints: {
      xsmall: {
        value: 375,
      },
      small: {
        value: 400,
      },
      medium: {
        value: 768,
      },
      large: {
        value: 1024,
      },
      xlarge: {
        value: 1366,
      },
    },
  },
  spinner: {
    container: {
      color: {
        light: "#002864",
        dark: "FFF"
      }
    }
  }
}

ReactDOM.render(
  <React.StrictMode>
    <CookiesProvider>
      <Grommet theme={grommetTheme} themeMode="light">
        <App />
      </Grommet>
    </CookiesProvider>
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
