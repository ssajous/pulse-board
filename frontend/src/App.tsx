import { Routes, Route } from "react-router-dom";
import { BoardPage } from "@presentation/pages";
import {
  EventPresentPage,
  EventAdminPage,
} from "@presentation/components/events";

function EventCreationPlaceholder() {
  return (
    <div className="p-8 text-center text-slate-400">
      Event creation page loading...
    </div>
  );
}

function EventJoinPlaceholder() {
  return (
    <div className="p-8 text-center text-slate-400">
      Event join page loading...
    </div>
  );
}

function EventBoardPlaceholder() {
  return (
    <div className="p-8 text-center text-slate-400">
      Event board loading...
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-slate-900 pb-20 font-sans text-slate-100">
      <Routes>
        <Route path="/" element={<BoardPage />} />
        <Route
          path="/events/new"
          element={<EventCreationPlaceholder />}
        />
        <Route
          path="/events/join"
          element={<EventJoinPlaceholder />}
        />
        <Route
          path="/events/:code"
          element={<EventBoardPlaceholder />}
        />
        <Route
          path="/events/:code/present"
          element={<EventPresentPage />}
        />
        <Route
          path="/events/:code/admin"
          element={<EventAdminPage />}
        />
      </Routes>
    </div>
  );
}

export default App;
