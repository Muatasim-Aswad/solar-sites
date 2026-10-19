import { useState } from "react";
import { useNavigate } from "react-router";
import { useDeleteSite } from "../mutations";
import { ErrorNotice, Notice } from "../../../shared/ui/feedback";
import { Button } from "../../../shared/ui/buttons";

export function DeleteSite({ siteId, clientName }: { siteId: string; clientName: string }) {
  const [confirming, setConfirming] = useState(false);
  const navigate = useNavigate();
  const deletion = useDeleteSite();
  async function deleteSite() {
    try {
      await deletion.mutateAsync(siteId);
      void navigate("/sites", { replace: true });
    } catch {
      /* The mutation exposes its error above. */
    }
  }

  return (
    <section className="mt-8" aria-label="Delete site">
      {confirming ? (
        <Notice>
          <h2>Delete {clientName}?</h2>
          <p>This permanently removes this client site.</p>
          <ErrorNotice error={deletion.error} />
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="danger" disabled={deletion.isPending} onClick={deleteSite}>
              {deletion.isPending ? "Deleting…" : "Delete site permanently"}
            </Button>
            <Button
              variant="secondary"
              disabled={deletion.isPending}
              onClick={() => setConfirming(false)}
            >
              Keep site
            </Button>
          </div>
        </Notice>
      ) : (
        <Button variant="danger-link" onClick={() => setConfirming(true)}>
          Delete site
        </Button>
      )}
    </section>
  );
}
