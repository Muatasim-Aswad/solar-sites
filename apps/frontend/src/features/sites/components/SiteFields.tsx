import type { FieldErrors, UseFormRegister } from "react-hook-form";
import { Field } from "../../../shared/ui/forms";
import type { SiteFormValues } from "./site-form";

export function SiteFields({
  register,
  errors,
}: {
  register: UseFormRegister<SiteFormValues>;
  errors: FieldErrors<SiteFormValues>;
}) {
  return (
    <>
      <Field
        label="Client name"
        autoComplete="name"
        maxLength={200}
        {...register("clientName")}
        error={errors.clientName?.message}
      />
      <Field
        label="Site address"
        autoComplete="street-address"
        maxLength={500}
        {...register("address")}
        error={errors.address?.message}
      />
      <div className="grid grid-cols-2 gap-x-4 max-compact:grid-cols-1">
        <Field
          label="Latitude"
          type="number"
          step="any"
          min={-90}
          max={90}
          hint="−90 to 90°"
          {...register("latitude", { valueAsNumber: true })}
          error={errors.latitude?.message}
        />
        <Field
          label="Longitude"
          type="number"
          step="any"
          min={-180}
          max={180}
          hint="−180 to 180°"
          {...register("longitude", { valueAsNumber: true })}
          error={errors.longitude?.message}
        />
        <Field
          label="Roof area (m²)"
          type="number"
          step="any"
          hint="Optional"
          {...register("roofAreaM2", {
            setValueAs: (value: string | number | null | undefined) =>
              value == null || value === "" ? null : Number(value),
          })}
          error={errors.roofAreaM2?.message}
        />
        <Field
          label="Panel capacity (kWp)"
          type="number"
          step="any"
          hint="Installed peak power"
          {...register("peakKwp", { valueAsNumber: true })}
          error={errors.peakKwp?.message}
        />
      </div>
    </>
  );
}
