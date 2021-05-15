import './App.css';
import Home from './pages/Home';
import Intro from './pages/Intro';
import Payment from './pages/Payment';
import FinishOnboarding from './pages/FinishOnboarding';

import { Route, Switch, BrowserRouter } from 'react-router-dom';


const App = () => {
  return (
    <BrowserRouter>
        <Switch>
            <Route exact path={'/'} render={() => <Home />}/>
            <Route exact path={'/login'} render={() => <Intro />}/>
            <Route exact path={'/payment'} render={() => <Payment />}/>
            <Route exact path={'/finishOnboarding'} render={() => <FinishOnboarding />}/>
        </Switch>
    </BrowserRouter>
  );
}

export default App;
