import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { setApiFieldErrors } from "../../../infra/api/form-errors";
import { Field, FormActions } from "../../../shared/ui/forms";
import { ErrorNotice } from "../../../shared/ui/feedback";
import { useSession } from "../session/SessionProvider";
import { Button } from "../../../shared/ui/buttons";

const credentialsSchema = z.object({
  email: z.email("Enter a valid email address.").max(254),
  password: z
    .string()
    .min(12, "Use at least 12 characters.")
    .max(128, "Use no more than 128 characters."),
});
type CredentialsValues = z.infer<typeof credentialsSchema>;

export function CredentialsForm({ mode }: { mode: "login" | "register" }) {
  const { authenticate } = useSession();
  const [error, setError] = useState<unknown>(null);

  const form = useForm<CredentialsValues>({
    resolver: zodResolver(credentialsSchema),
    defaultValues: { email: "", password: "" },
  });

  const registering = mode === "register";
  const actionLabel = registering ? "Create account" : "Log in";

  async function submitCredentials(values: CredentialsValues) {
    setError(null);

    try {
      await authenticate(mode, values);
    } catch (failure) {
      setError(failure);
      setApiFieldErrors(failure, ["email", "password"], form.setError);
    }
  }

  return (
    <form noValidate onSubmit={form.handleSubmit(submitCredentials)}>
      <fieldset disabled={form.formState.isSubmitting}>
        <Field
          label="Email address"
          type="email"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          {...form.register("email")}
          error={form.formState.errors.email?.message}
        />
        <Field
          label="Password"
          type="password"
          autoComplete={registering ? "new-password" : "current-password"}
          hint="12–128 characters"
          {...form.register("password")}
          error={form.formState.errors.password?.message}
        />
        <ErrorNotice error={error} />
        <FormActions>
          <Button type="submit">
            {form.formState.isSubmitting ? "Please wait…" : actionLabel}
          </Button>
        </FormActions>
      </fieldset>
    </form>
  );
}
