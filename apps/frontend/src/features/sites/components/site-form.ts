import { z } from "zod";
import type { components } from "../../../infra/api/schema";

type SiteInput = components["schemas"]["SiteInput"];
export const siteSchema = z.object({
  clientName: z.string().trim().min(1, "Enter a client name.").max(200),
  address: z.string().trim().min(1, "Enter an address.").max(500),
  latitude: z.number({ error: "Enter a latitude." }).min(-90).max(90),
  longitude: z.number({ error: "Enter a longitude." }).min(-180).max(180),
  roofAreaM2: z.number().positive("Roof area must be greater than zero.").max(1_000_000).nullable(),
  peakKwp: z
    .number({ error: "Enter a panel capacity." })
    .positive("Panel capacity must be greater than zero.")
    .max(100_000),
}) satisfies z.ZodType<SiteInput>;
export type SiteFormValues = z.infer<typeof siteSchema>;
