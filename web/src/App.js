import './App.css';
import Home from './pages/Home';
import Intro from './pages/Intro';
import Payment from './pages/Payment';
import FinishOnboarding from './pages/FinishOnboarding';

import { Route, Switch, BrowserRouter } from 'react-router-dom';
import { ResponsiveContext } from "grommet";
import LandingPage from './pages/LandingPage';
import PrivacyPolicy from './pages/PrivacyPolicy';


const App = () => {
  return (
    <BrowserRouter>
        <Switch>
            <Route exact path={'/'} render={() => <Home />}/>
            <Route exact path={'/login'} render={() => <Intro />}/>
            <Route exact path={'/payment'} render={() => <Payment />}/>
            <Route exact path={'/finishOnboarding'} render={() => <FinishOnboarding />}/>
            <Route exact path={'/welcome'} render={() => (
              <ResponsiveContext.Consumer>
                {(size) => {
                  return <LandingPage size={size}/>
                }}
              </ResponsiveContext.Consumer>
            )}/>
            <Route exact path={"/privacy"} render={() => <PrivacyPolicy />}/>
        </Switch>
    </BrowserRouter>
  );
}

export default App;
