// geneticframes-web/src/App.tsx
import { Route, Switch } from 'wouter';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Home } from './pages/Home';
import { SpeciesArt } from './pages/SpeciesArt';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Switch>
        <Route path="/" component={Home} />
        <Route path="/species/:name" component={SpeciesArt} />
        <Route>404: Evolution not found</Route>
      </Switch>
    </QueryClientProvider>
  );
}

export default App;
