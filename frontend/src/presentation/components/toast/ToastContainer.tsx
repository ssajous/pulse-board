import { observer } from "mobx-react-lite";
import { useTopicsViewModel } from "@presentation/view-models";
import { Toast } from "./Toast";

export const ToastContainer = observer(function ToastContainer() {
  const vm = useTopicsViewModel();

  if (!vm.toast) return null;

  return (
    <Toast
      message={vm.toast.message}
      type={vm.toast.type}
      onClose={vm.dismissToast}
    />
  );
});
