import logo from './logo.svg';
import './App.css';
import Home from './pages/Home';
import Intro from './pages/Intro';

import { Route, Switch, BrowserRouter } from 'react-router-dom';

const App = () => {
  return (
    <BrowserRouter>
        <Switch>
            <Route exact path={'/'} render={() => <Home />}/>
            <Route exact path={'/login'} render={() => <Intro />}/>
        </Switch>
    </BrowserRouter>
  );
}

export default App;
