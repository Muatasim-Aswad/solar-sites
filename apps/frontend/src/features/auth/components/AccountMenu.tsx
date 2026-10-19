import { useState } from "react";
import { useSession } from "../session/SessionProvider";
import { ErrorNotice } from "../../../shared/ui/feedback";
import { Button } from "../../../shared/ui/buttons";

export function AccountMenu({ email }: { email: string }) {
  const { logout } = useSession();
  const [error, setError] = useState<unknown>(null);
  const [pending, setPending] = useState(false);
  async function logoutAccount() {
    setPending(true);
    setError(null);
    try {
      await logout();
    } catch (failure) {
      setError(failure);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="relative ml-auto flex items-center gap-4 max-compact:gap-[0.7rem]">
      <span className="text-[0.9rem] wrap-anywhere max-compact:max-w-[16ch] max-compact:text-[0.8rem]">
        {email}
      </span>
      <Button variant="secondary" disabled={pending} onClick={logoutAccount}>
        {pending ? "Logging out…" : "Log out"}
      </Button>
      {error ? (
        <div className="absolute top-full right-0 z-2 min-w-70">
          <ErrorNotice error={error} />
        </div>
      ) : null}
    </div>
  );
}
