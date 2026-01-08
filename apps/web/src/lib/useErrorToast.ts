import { useEffect, useRef } from "react";
import { useToast } from "../components/ui/Toast";

export const useErrorToast = (hasError: boolean, message: string) => {
  const toast = useToast();
  const hasShown = useRef(false);

  useEffect(() => {
    if (hasError && !hasShown.current) {
      toast.push(message, "error");
      hasShown.current = true;
    }
    if (!hasError) {
      hasShown.current = false;
    }
  }, [hasError, message, toast]);
};
