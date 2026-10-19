import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "../../../infra/api/errors";
import type { BatteryInput } from "../queries";
import { Field, FormActions } from "../../../shared/ui/forms";
import { Button } from "../../../shared/ui/buttons";

const batterySchema = z.object({
  annualUseKwh: z.number({ error: "Enter yearly electricity use." }).min(0).max(100_000_000),
  capacityKwh: z.number({ error: "Enter battery capacity." }).min(0).max(100_000),
}) satisfies z.ZodType<BatteryInput>;

export function BatteryForm({
  pending,
  error,
  onSubmit,
}: {
  pending: boolean;
  error: unknown;
  onSubmit: (values: BatteryInput) => void;
}) {
  const form = useForm<BatteryInput>({ resolver: zodResolver(batterySchema) });

  const issue = (field: keyof BatteryInput) =>
    error instanceof ApiError
      ? error.issues.find((item) => item.field === field)?.message
      : undefined;

  return (
    <form noValidate onSubmit={form.handleSubmit(onSubmit)}>
      <fieldset disabled={pending}>
        <div className="grid grid-cols-2 gap-x-4 max-compact:grid-cols-1">
          <Field
            label="Yearly electricity use (kWh)"
            type="number"
            min={0}
            max={100_000_000}
            step="any"
            {...form.register("annualUseKwh", { valueAsNumber: true })}
            error={form.formState.errors.annualUseKwh?.message ?? issue("annualUseKwh")}
          />
          <Field
            label="Battery capacity (kWh)"
            type="number"
            min={0}
            max={100_000}
            step="any"
            {...form.register("capacityKwh", { valueAsNumber: true })}
            error={form.formState.errors.capacityKwh?.message ?? issue("capacityKwh")}
          />
        </div>
        <FormActions>
          <Button type="submit">{pending ? "Comparing…" : "Compare battery"}</Button>
        </FormActions>
      </fieldset>
    </form>
  );
}
