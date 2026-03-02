import { observer } from "mobx-react-lite";
import { useEventCreationViewModel } from "@presentation/view-models/EventCreationViewModelContext";
import { EventCreationFormFields } from "./EventCreationFormFields";
import { EventCreationConfirmation } from "./EventCreationConfirmation";

export const EventCreationForm = observer(function EventCreationForm() {
  const vm = useEventCreationViewModel();

  if (vm.isComplete) {
    return <EventCreationConfirmation />;
  }
  return <EventCreationFormFields />;
});
