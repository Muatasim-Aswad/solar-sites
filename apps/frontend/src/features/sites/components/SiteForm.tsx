import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router";
import type { components } from "../../../infra/api/schema";
import { setApiFieldErrors } from "../../../infra/api/form-errors";
import { FormActions } from "../../../shared/ui/forms";
import { ErrorNotice } from "../../../shared/ui/feedback";
import { useCreateSite, useUpdateSite } from "../mutations";
import { SiteFields } from "./SiteFields";
import { siteSchema, type SiteFormValues } from "./site-form";
import { Button, ButtonLink } from "../../../shared/ui/buttons";

type Site = components["schemas"]["SiteOutput"];
const fieldNames = [
  "clientName",
  "address",
  "latitude",
  "longitude",
  "roofAreaM2",
  "peakKwp",
] as const;

export function SiteForm({ site }: { site?: Site }) {
  const navigate = useNavigate();
  const create = useCreateSite();
  const update = useUpdateSite();

  const form = useForm<SiteFormValues>({
    resolver: zodResolver(siteSchema),
    defaultValues: site
      ? {
          clientName: site.clientName,
          address: site.address,
          latitude: site.latitude,
          longitude: site.longitude,
          roofAreaM2: site.roofAreaM2 ?? null,
          peakKwp: site.peakKwp,
        }
      : { clientName: "", address: "", roofAreaM2: null },
  });

  const actionLabel = site ? "Save changes" : "Create site";
  const cancelPath = site ? `/sites/${site.id}` : "/sites";

  async function submitSite(body: SiteFormValues) {
    create.reset();
    update.reset();

    try {
      const saved = site
        ? await update.mutateAsync({ siteId: site.id, body })
        : await create.mutateAsync(body);
      void navigate(`/sites/${saved.id}`);
    } catch (error) {
      setApiFieldErrors(error, fieldNames, form.setError);
    }
  }

  return (
    <form noValidate onSubmit={form.handleSubmit(submitSite)}>
      <fieldset disabled={form.formState.isSubmitting}>
        <SiteFields register={form.register} errors={form.formState.errors} />
        <ErrorNotice error={create.error ?? update.error} />
        <FormActions>
          <Button type="submit">{form.formState.isSubmitting ? "Saving…" : actionLabel}</Button>
          <ButtonLink variant="secondary" to={cancelPath}>
            Cancel
          </ButtonLink>
        </FormActions>
      </fieldset>
    </form>
  );
}
