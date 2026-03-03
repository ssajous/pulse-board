import { Routes, Route } from "react-router-dom";
import {
  BoardPage,
  EventCreationPage,
  EventJoinPage,
  EventBoardPage,
} from "@presentation/pages";
import { EventPresentPage } from "@presentation/components/events";
import { HostDashboard } from "@presentation/components/host-dashboard";

function App() {
  return (
    <div className="min-h-screen bg-slate-900 pb-20 font-sans text-slate-100">
      <Routes>
        <Route path="/" element={<BoardPage />} />
        <Route path="/events/new" element={<EventCreationPage />} />
        <Route path="/events/join" element={<EventJoinPage />} />
        <Route path="/events/:code" element={<EventBoardPage />} />
        <Route
          path="/events/:code/present"
          element={<EventPresentPage />}
        />
        <Route
          path="/events/:code/admin"
          element={<HostDashboard />}
        />
      </Routes>
    </div>
  );
}

export default App;
